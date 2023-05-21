import math
import tempfile

import numpy as np
import pandas as pd
import rasterio
import rasterio as rio
import xarray as xr
from django.core.files import File
from django.forms import FileField
from django_large_image import tilesource
from django_large_image.utilities import field_file_to_local_path
from large_image.exceptions import TileSourceError
from rest_framework.exceptions import APIException
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

from geomanager.errors import UnsupportedRasterFormat
from geomanager.models import LayerRasterFile


def get_tile_source(path, options=None):
    if options is None:
        options = {}

    encoding = options.get("encoding")
    style = options.get("style")
    projection = options.get("projection")

    kwargs = {}

    if encoding:
        kwargs["encoding"] = encoding
    if style:
        kwargs["style"] = style
    if projection:
        kwargs["projection"] = projection

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
