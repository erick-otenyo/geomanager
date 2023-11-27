import logging
import os
import re
import tempfile
import uuid
from datetime import datetime
from os.path import splitext, isfile

import pytz
from adminboundarymanager.models import AdminBoundarySettings, AdminBoundary
from dateutil.parser import isoparse
from django.core.files import File
from django.db import transaction
from shapely import wkb
from wagtail.models import Site

from geomanager.models import RasterUpload, LayerRasterFile, RasterFileLayer
from geomanager.utils.raster_utils import (
    create_layer_raster_file,
    read_raster_info,
    bounds_to_polygon,
    check_raster_bounds_with_boundary,
    clip_netcdf,
    clip_geotiff
)

logger = logging.getLogger("geomanager.ingest")
logger.setLevel(logging.INFO)

ALLOWED_RASTER_FILE_EXTENSIONS = ['.tif', '.nc']


class IngestException(Exception):
    def __init__(self, message):
        self.message = message


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def extract_iso_date_from_filename(file_name):
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"  # Pattern 'YYYY-MM-DDTHH:MM:SS.sssZ'
    match = re.search(pattern, file_name)  # Search for the pattern at the end of the file name

    if match:
        iso_date = match.group()  # Extract the matched ISO format string
        tz_unaware_date = isoparse(iso_date)  # Convert the string to datetime object
        tz_aware_date = tz_unaware_date.replace(tzinfo=pytz.UTC)  # Make the datetime object timezone aware
        return tz_aware_date
    else:
        return None  # Return None if the file name doesn't end with the specified format


def clip_raster_upload_to_boundary(upload, request=None):
    if request:
        abm_settings = AdminBoundarySettings.for_request(request)
    else:
        site = Site.objects.get(is_default_site=True)
        if not site:
            return None
        abm_settings = AdminBoundarySettings.for_site(site)

    abm_extents = abm_settings.combined_countries_bounds
    abm_countries = abm_settings.countries_list

    if not abm_extents:
        return upload

    raster_metadata = read_raster_info(upload.file.path)
    raster_bounds = raster_metadata.get("bounds")
    if not raster_bounds:
        return upload
    intersects_with_boundary, completely_inside_boundary = check_raster_bounds_with_boundary(raster_bounds, abm_extents)

    if not intersects_with_boundary:
        return upload

    if completely_inside_boundary:
        return upload

    raster_driver = raster_metadata.get("driver")
    country_geoms = []
    for country in abm_countries:
        code = country.get("code")
        alpha3 = country.get("alpha3")

        # query using code (2-letter code)
        country_boundary = AdminBoundary.objects.filter(level=0, gid_0=code).first()

        # query using alpha 3 (3-letter code)
        if not country_boundary:
            country_boundary = AdminBoundary.objects.filter(level=0, gid_0=alpha3).first()

        if country_boundary:
            shapely_geom = wkb.loads(country_boundary.geom.hex)
            country_geoms.append(shapely_geom)
        else:
            # use bbox instead
            bbox = country.get("bbox")
            if bbox:
                bounds_geom = bounds_to_polygon(bbox)
                country_geoms.append(bounds_geom)

    union_polygon = country_geoms[0]
    for polygon in country_geoms[1:]:
        union_polygon = union_polygon.union(polygon)

    if raster_driver == "netCDF":
        clip_fn = clip_netcdf
        suffix = ".nc"
    else:
        clip_fn = clip_geotiff
        suffix = ".tif"

    with tempfile.NamedTemporaryFile(suffix=suffix) as f:
        clipped_raster = clip_fn(upload.file.path, union_polygon, f.name)
        raster_metadata = read_raster_info(clipped_raster)

        with open(clipped_raster, 'rb') as clipped_file:
            file_obj = File(clipped_file, name=f.name)
            upload.file.save(upload.file.name, file_obj, save=True)

    upload.raster_metadata = raster_metadata
    upload.save()

    return upload


def create_raster(layer_obj, upload, time, overwrite=False, band_index=None, data_variable=None):
    # check if raster file with this time already exists
    exists = LayerRasterFile.objects.filter(layer=layer_obj, time=time).exists()

    # return if raster file already exists and overwrite is False
    if exists and not overwrite:
        logger.warning(f'LayerRasterFile for layer: {layer_obj.pk} and time: {time} already exists.')
        return

    # delete raster file if exists and overwrite is True, and create new raster file
    if exists and overwrite:
        with transaction.atomic():
            layer_raster_file = LayerRasterFile.objects.get(layer=layer_obj, time=time)
            layer_raster_file.delete()

            create_layer_raster_file(layer_obj, upload, time, band_index=band_index, data_variable=data_variable)
    else:
        # create new raster file
        create_layer_raster_file(layer_obj, upload, time, band_index=band_index, data_variable=data_variable)


def raw_raster_file_to_layer_raster_file(layer_obj, file_path, time=None, overwrite=False, clip_to_boundary=False):
    with open(file_path, "rb") as file:
        file_name = os.path.basename(file.name)

        upload = RasterUpload.objects.create(dataset=layer_obj.dataset)
        upload.file.save(file_name, file, save=True)

        raster_metadata = read_raster_info(upload.file.path)
        upload.raster_metadata = raster_metadata
        upload.save()

        try:
            if clip_to_boundary:
                # clip raster upload to boundary
                upload = clip_raster_upload_to_boundary(upload)

            raster_driver = raster_metadata.get("driver")

            if raster_driver == "netCDF":
                data_variable = layer_obj.auto_ingest_nc_data_variable

                if not data_variable:
                    raise IngestException(f'No NetCDF Auto ingestion data variable set for layer: {layer_obj}')

                if data_variable not in raster_metadata.get("data_variables", []):
                    raise IngestException(
                        f'NetCDF Auto ingestion data variable: {data_variable} not found in NetCDF: {file_name}')

                timestamps = raster_metadata.get("timestamps", None)

                if not timestamps:
                    raise IngestException(f'No timestamps found in NetCDF: {file_name}')

                for i, time_str in enumerate(timestamps):
                    d_time_unaware = datetime.fromisoformat(time_str)
                    d_time_aware = d_time_unaware.replace(tzinfo=pytz.UTC)

                    logger.info(f'[GEOMANAGER_AUTO_INGEST]: Processing time : {time_str}')

                    create_raster(layer_obj, upload, d_time_aware, overwrite=overwrite, band_index=i,
                                  data_variable=data_variable)

            elif raster_driver == "GTiff":
                if time:
                    logger.info(f'[GEOMANAGER_AUTO_INGEST]: Processing time : {time}')
                    create_raster(layer_obj, upload, time, overwrite=overwrite)

        finally:
            # delete raster upload
            upload.delete()


def ingest_raster_file(src_path, overwrite=False, clip_to_boundary=False):
    # Check if source path exists
    if not isfile(src_path):
        raise IngestException(f'File path: {src_path} does not exist.')

    file_extension = splitext(src_path)[1].lower()

    if file_extension not in ALLOWED_RASTER_FILE_EXTENSIONS:
        raise IngestException(f'File path: {src_path} is not a tiff or netcdf file.')

    directory = os.path.dirname(src_path)
    file_name = os.path.basename(src_path)
    file_name_without_extension = os.path.splitext(file_name)[0]

    # check if the directory name is an uuid
    layer_uuid = os.path.basename(os.path.normpath(directory))
    if not is_valid_uuid(layer_uuid):
        raise IngestException(f'Directory name: {directory} is not a valid uuid.')

    # check if layer exists
    raster_file_layer = RasterFileLayer.objects.filter(pk=layer_uuid).first()
    if not raster_file_layer:
        raise IngestException(f'RasterFileLayer with UUID: {layer_uuid} does not exist.')

    if file_extension == '.tif':
        # check if file name ends with iso format date, return the parsed date if it does
        iso_date_time = extract_iso_date_from_filename(file_name_without_extension)
        if not iso_date_time:
            raise IngestException(f'File name: {file_name} does not end with iso format date.')

        # create layer raster file from raw tiff file
        raw_raster_file_to_layer_raster_file(raster_file_layer, src_path, time=iso_date_time, overwrite=overwrite,
                                             clip_to_boundary=clip_to_boundary)

    elif file_extension == '.nc':
        # process netcdf file
        raw_raster_file_to_layer_raster_file(raster_file_layer, src_path, time=None, overwrite=overwrite,
                                             clip_to_boundary=clip_to_boundary)

    else:
        raise IngestException(f'File extension: {file_extension} not supported.')
