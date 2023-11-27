import math
import pathlib
import tempfile

import numpy as np
import pandas as pd
import rasterio as rio
import xarray as xr
import rioxarray as rxr
from django.core.files import File
from django.forms import FileField
from django_large_image import tilesource
from django_large_image.utilities import (
    field_file_to_local_path,
    get_cache_dir,
    get_file_lock,
    get_file_safe_path
)
from large_image.exceptions import TileSourceError
from rasterio import CRS
from rasterio.mask import mask
from rest_framework.exceptions import APIException
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from shapely import wkb, Polygon

from geomanager.errors import UnsupportedRasterFormat
from geomanager.models import LayerRasterFile, Geostore


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
    except (TileSourceError, Exception) as e:
        # Raise 500 server error if tile source failed to open
        raise APIException(str(e))


def get_raster_pixel_data(file: FileField, x_coord: float, y_coord: float):
    source = get_tile_source(path=file)

    # get raster affine transform
    metadata = source.getInternalMetadata()
    affine = metadata.get("Affine")

    # get corresponding row col
    row_col = rio.transform.rowcol(affine, xs=x_coord, ys=y_coord)
    pixel_data = source.getPixel(region={'left': abs(row_col[1]), 'top': abs(row_col[0])})

    if pixel_data:
        return pixel_data.get("bands", {}).get(1)

    return None


def get_geostore_data(file: FileField, geostore, value_type=None):
    data = {}

    try:
        file_path = field_file_to_local_path_for_geostore(file, geostore)

        with rio.open(str(file_path), 'r') as src:
            band_array = src.read(1)
            values = band_array[band_array != src.nodata]

        if value_type:
            if value_type == "mean":
                data.update({"mean": values.mean()})
            elif value_type == "sum":
                data.update({"sum": values.sum()})
            elif value_type == "minmax":
                data.update({
                    "min": values.min(),
                    "max": values.max()
                })
            elif value_type == "minmeanmax":
                data.update({
                    "min": values.min(),
                    "max": values.max(),
                    "mean": values.mean()
                })
            else:
                data.update({"mean": values.mean()})
        else:
            data.update({"mean": values.mean()})
    except Exception:
        pass

    return data


def get_no_data_val(val):
    if not val:
        return None
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
        rds = xr.open_dataset(upload.file.path, engine="rasterio")

        try:  # index must start from 0
            if data_variable:
                rds = rds[data_variable]

            if timestamps and band_index is not None:
                rds = rds.isel(time=int(band_index))

            # write crs if not available
            if not rds.rio.crs:
                epsg = "epsg:4326"
                if crs and isinstance(crs, dict) and crs.get("init"):
                    epsg = crs.get("init")
                rds = rds.rio.write_crs(epsg)

            # drop grid_mapping attr. somehow it causes errors when saving
            if rds.rio.crs and rds.attrs.get("grid_mapping"):
                rds.attrs.pop("grid_mapping")

            # make sure no data value is not nan
            nodata_value = rds.encoding.get('nodata', rds.encoding.get('_FillValue'))
            if not nodata_value or np.isnan(nodata_value):
                rds = rds.rio.write_nodata(-9999, encoded=True)

            netcdf_attrs = []
            for key in rds.attrs.keys():
                if key.startswith("NETCDF_"):
                    netcdf_attrs.append(key)

                # assign only one unit
                if key == "units" and isinstance(rds.attrs["units"], list):
                    rds.attrs["units"] = rds.attrs["units"][0]

            # delete 'NETCDF_*' attributes
            for nc_attr in netcdf_attrs:
                rds.attrs.pop(nc_attr)

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
            file_name = f"{raster.time_str}.tif"
            if data_variable:
                file_name = f"{data_variable}_{file_name}"
            raster.file.save(file_name, file_content)

            try:
                source = get_tile_source(raster.file)
                metadata = source.getMetadata()
                if metadata:
                    raster.raster_metadata = metadata
            except Exception:
                pass

            raster.save()


def clip_geotiff(geotiff_path, geom, out_file):
    data = rio.open(geotiff_path)
    out_img, out_transform = mask(data, shapes=[geom], crop=True)
    out_meta = data.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": out_img.shape[1],
        "width": out_img.shape[2],
        "transform": out_transform,
        "crs": CRS().from_epsg(code=4326),
    })

    with rio.open(out_file, "w", **out_meta) as dest:
        dest.write(out_img)

    return out_file


def clip_netcdf(nc_path, geom, out_file):
    rds = xr.open_dataset(nc_path, engine="rasterio")

    # write crs
    rds.rio.write_crs("epsg:4326", inplace=True)

    # clip
    rds = rds.rio.clip([geom], "epsg:4326", drop=True)

    # write clipped data to file
    rds.to_netcdf(out_file)

    rds.close()

    return out_file


def field_file_to_local_path_for_geostore(path, geostore):
    field_file_basename = pathlib.PurePath(path.name).name
    directory = get_cache_dir() / f"{type(path.instance).__name__}-{path.instance.pk}" / "geostore"
    dest_path = directory / f"{geostore.pk.hex}-{field_file_basename}"
    lock = get_file_lock(dest_path)
    safe = get_file_safe_path(dest_path)

    with lock.acquire():
        if not safe.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            # convert OGRGeometry to Shapely geometry for consistency in clipping
            shapely_geom = wkb.loads(geostore.geom.hex)
            clip_geotiff(path.file.name, shapely_geom, dest_path)

    return dest_path


def bounds_to_polygon(bounds):
    polygon_coords = ((bounds[0], bounds[1]), (bounds[2], bounds[1]), (bounds[2], bounds[3]), (bounds[0], bounds[3]))
    return Polygon(polygon_coords)


def check_raster_bounds_with_boundary(raster_bounds, boundary_bounds):
    boundary_poly = bounds_to_polygon(boundary_bounds)
    raster_poly = bounds_to_polygon(raster_bounds)

    intersects = boundary_poly.intersects(raster_poly)
    contains = boundary_poly.contains(raster_poly)

    return intersects, contains
