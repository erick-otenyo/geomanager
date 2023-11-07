import logging
import os
import re
import tempfile
import uuid
from os.path import splitext, isfile

from adminboundarymanager.models import AdminBoundarySettings, AdminBoundary
from dateutil.parser import isoparse
from django.core.files import File
from django.db import transaction
from shapely import wkb
from wagtail.models import Site

from geomanager.models import RasterUpload, LayerRasterFile, RasterFileLayer
from geomanager.utils.raster_utils import create_layer_raster_file, read_raster_info, bounds_to_polygon, \
    check_raster_bounds_with_boundary, clip_netcdf, clip_geotiff

logger = logging.getLogger("geomanager.ingest")
logger.setLevel(logging.INFO)


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def extract_iso_date(file_name):
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"  # Pattern 'YYYY-MM-DDTHH:MM:SS.sssZ'
    match = re.search(pattern, file_name)  # Search for the pattern at the end of the file name

    if match:
        iso_date = match.group()  # Extract the matched ISO format string
        return isoparse(iso_date)  # Convert the string to datetime object
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


def raw_raster_file_to_layer_raster_file(layer_obj, time, file_path, overwrite=False, clip_to_boundary=False):
    with open(file_path, "rb") as file:
        file_name = os.path.basename(file.name)

        upload = RasterUpload.objects.create(dataset=layer_obj.dataset)
        upload.file.save(file_name, file, save=True)

        raster_metadata = read_raster_info(upload.file.path)
        upload.raster_metadata = raster_metadata
        upload.save()

        try:
            # check if raster file with this time already exists
            exists = LayerRasterFile.objects.filter(layer=layer_obj, time=time).exists()

            # return if raster file already exists and overwrite is False
            if exists and not overwrite:
                logger.warning(f'LayerRasterFile for layer: {layer_obj.pk} and time: {time} already exists.')
                return

            if clip_to_boundary:
                # clip raster upload to boundary
                upload = clip_raster_upload_to_boundary(upload)

            # delete raster file if exists and overwrite is True, and create new raster file
            if exists and overwrite:
                with transaction.atomic():
                    layer_raster_file = LayerRasterFile.objects.get(layer=layer_obj, time=time)
                    layer_raster_file.delete()
                    create_layer_raster_file(layer_obj, upload, time)
            else:
                # create new raster file
                create_layer_raster_file(layer_obj, upload, time)
        finally:
            # delete raster upload
            upload.delete()


def ingest_raster_file(src_path, overwrite=False, clip_to_boundary=False):
    # Check if source path exists
    if not isfile(src_path):
        logger.warning(f'[GEOMANAGER_INGEST] File path: {src_path} does not exist.')
        return

    # check if file is a .tif file
    if not splitext(src_path)[1].lower() == '.tif':
        logger.warning(f'[GEOMANAGER_INGEST] File path: {src_path} is not a tiff file.')
        return

    directory = os.path.dirname(src_path)
    file_name = os.path.basename(src_path)
    file_name_without_extension = os.path.splitext(file_name)[0]

    # check if file name ends with iso format date, return the parsed date if it does
    iso_date_time = extract_iso_date(file_name_without_extension)
    if not iso_date_time:
        logger.warning(f'[GEOMANAGER_INGEST] File name: {file_name} does not end with iso format date.')
        return

    # check if the directory name is an uuid
    layer_uuid = os.path.basename(os.path.normpath(directory))
    if not is_valid_uuid(layer_uuid):
        logger.warning(f'[GEOMANAGER_INGEST] Directory name: {directory} is not a valid uuid.')
        return

    # check if layer exists
    raster_file_layer = RasterFileLayer.objects.filter(pk=layer_uuid).first()
    if not raster_file_layer:
        logger.warning(f'[GEOMANAGER_INGEST] RasterFileLayer with UUID: {layer_uuid} does not exist.')
        return

    # create layer raster file from raw tiff file
    raw_raster_file_to_layer_raster_file(raster_file_layer, iso_date_time, src_path, overwrite=overwrite,
                                         clip_to_boundary=clip_to_boundary)
