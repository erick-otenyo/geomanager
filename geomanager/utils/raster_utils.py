import math
import pathlib
import tempfile

import numpy as np
import pandas as pd
import rasterio
import rasterio as rio
import xarray as xr
from django.core.files import File
from django.forms import FileField
from django_large_image import tilesource
from django_large_image.utilities import field_file_to_local_path, get_cache_dir, get_file_lock, get_file_safe_path
from large_image.exceptions import TileSourceError
from rasterio import CRS
from rasterio.mask import mask
from rest_framework.exceptions import APIException
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from shapely import wkb

from geomanager.errors import UnsupportedRasterFormat
from geomanager.models import LayerRasterFile, Geostore

from osgeo import gdal


def get_tile_source(path, options=None):
    if options is None:
        options = {}

    encoding = options.get("encoding")
    style = options.get("style")
    projection = options.get("projection")
    geostore_id = options.get("geostore_id")

    kwargs = {}

    if encoding:
        kwargs["encoding"] = encoding
    if style:
        kwargs["style"] = style
    if projection:
        kwargs["projection"] = projection

    geostore = None

    if geostore_id:
        try:
            geostore = Geostore.objects.get(pk=geostore_id)
        except Exception:
            pass

    if geostore:
        file_path = field_file_to_local_path_for_geostore(path, geostore)
    else:
        file_path = field_file_to_local_path(path)

    try:
        return tilesource.get_tilesource_from_path(file_path, source=None, **kwargs)
    except TileSourceError as e:
        # Raise 500 server error if tile source failed to open
        raise APIException(str(e))


def get_raster_pixel_data(file: FileField, x_coord: float, y_coord: float):
    source = get_tile_source(path=file)
    # get raster gdal geotransform
    gdal_geot = source.getInternalMetadata().get("GeoTransform")
    transform = rasterio.Affine.from_gdal(*gdal_geot)

    # get corresponding row col
    row_col = rasterio.transform.rowcol(transform, xs=x_coord, ys=y_coord)
    pixel_data = source.getPixel(region={'left': abs(row_col[1]), 'top': abs(row_col[0])})

    if pixel_data:
        return pixel_data.get("bands", {}).get(1)

    return None


def get_geostore_data(file: FileField, geostore):
    file_path = field_file_to_local_path_for_geostore(file, geostore)

    raster = gdal.Open(str(file_path))
    band = raster.GetRasterBand(1)
    no_data_value = band.GetNoDataValue()
    band_array = band.ReadAsArray()
    valid_values = band_array[band_array != no_data_value]

    raster = None

    return valid_values


def get_no_data_val(val):
    if math.isnan(val):
        return None
    return val


def read_raster_info(file_path):
    raster = rio.open(file_path)

    no_data_vals = raster.nodatavals
    no_data_vals = [get_no_data_val(val) for val in no_data_vals]

    # get basic raster info using rasterio
    raster_info = {
        "crs": raster.crs.to_dict() if raster.crs else None,
        "bounds": raster.bounds,
        "width": raster.width,
        "height": raster.height,
        "bands_count": raster.count,
        "driver": raster.driver,
        "nodatavals": tuple(no_data_vals)
    }

    # close raster
    raster.close()

    # get netcdf info
    if raster_info["driver"] == "netCDF":

        ds = xr.open_dataset(file_path, decode_times=True)

        if isinstance(ds, xr.DataArray):
            ds = ds.to_dataset()

        skip_vars = ["nbnds", "time_bnds", "spatial_ref"]
        data_vars = list(ds.data_vars.keys())
        data_vars = [var for var in data_vars if var not in skip_vars]

        raster_info.update({"data_variables": data_vars})
        raster_info.update({"dimensions": list(ds.dims)})

        # get timestamps
        if "time" in ds.dims:
            timestamps = [pd.to_datetime(ts).isoformat() for ts in ds.time.data]

            raster_info.update({"timestamps": timestamps})

        # close dataset
        ds.close()

    return raster_info


def convert_upload_to_geotiff(upload, out_file_path, band_index=None, data_variable=None):
    metadata = upload.raster_metadata

    driver = metadata.get("driver")

    crs = metadata.get("crs")
    timestamps = metadata.get("timestamps", None)

    # handle netcdf
    if driver == "netCDF":
        rds = xr.open_dataset(upload.file.path)

        # write crs if not available
        if not crs:
            rds.rio.write_crs("epsg:4326", inplace=True)
        try:  # index must start from 0

            if data_variable:
                rds = rds[data_variable]

            if timestamps and band_index:
                rds = rds.isel(time=int(band_index))

            # make sure no data value is not nan
            nodata_value = rds.encoding.get('nodata', rds.encoding.get('_FillValue'))
            if np.isnan(nodata_value):
                rds = rds.rio.write_nodata(-9999, encoded=True)

            rds.rio.to_raster(out_file_path, driver="COG", compress="DEFLATE")
        except Exception as e:
            raise e
        finally:
            rds.close()

        return True

    # handle geotiff
    if driver == "GTiff":
        output_profile = cog_profiles.get("deflate")

        # write crs if not available
        if not crs:
            output_profile["crs"] = "epsg:4326"

        # save as COG
        cog_translate(
            upload.file.path,
            out_file_path,
            output_profile,
            indexes=band_index,
            in_memory=False
        )

        return True

    raise UnsupportedRasterFormat


def create_layer_raster_file(layer, upload, time, band_index=None, data_variable=None):
    with tempfile.NamedTemporaryFile(suffix=".tif") as f:
        convert_upload_to_geotiff(upload, f.name, band_index=band_index, data_variable=data_variable)
        with open(f.name, mode='rb') as file:
            file_content = File(file)
            raster = LayerRasterFile(layer=layer, time=time)
            file_name = f"{time.isoformat()}.tif"
            if data_variable:
                file_name = f"{data_variable}_{file_name}"
            raster.file.save(file_name, file_content)
            raster.save()


def clip_geotiff(geotiff_path, geom, out_file):
    geom = wkb.loads(geom.hex)
    data = rasterio.open(geotiff_path)
    out_img, out_transform = mask(data, shapes=[geom], crop=True)
    out_meta = data.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": out_img.shape[1],
        "width": out_img.shape[2],
        "transform": out_transform,
        "crs": CRS.from_epsg(code=4326),
    })

    with rasterio.open(out_file, "w", **out_meta) as dest:
        dest.write(out_img)

    return out_file


def field_file_to_local_path_for_geostore(path, geostore):
    field_file_basename = pathlib.PurePath(path.name).name
    directory = get_cache_dir() / f'{type(path.instance).__name__}-{geostore.pk.hex}-{path.instance.pk}'
    dest_path = directory / field_file_basename
    lock = get_file_lock(dest_path)
    safe = get_file_safe_path(dest_path)

    with lock.acquire():
        if not safe.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            clip_geotiff(path.file.name, geostore.geom, dest_path)

    return dest_path
