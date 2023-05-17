import os
import tempfile

import geopandas as gpd
from django.contrib.gis.utils import LayerMapping

from geomanager.errors import MissingBoundaryField, NoMatchingBoundaryData, InvalidBoundaryGeomType
from geomanager.models.vector import CountryBoundary
from geomanager.utils.vector_utils import extract_zipped_shapefile

BOUNDARY_FIELDS = {
    "name_0": "name_0",
    "name_1": "name_1",
    "name_2": "name_2",
    "gid_0": "gid_0",
    "gid_1": "gid_1",
    "gid_2": "gid_2",
    "level": "level",
    "size": "size",
}

LAYER_MAPPING_FIELDS = {
    **BOUNDARY_FIELDS,
    "geom": "MULTIPOLYGON",
}

VALID_GEOM_TYPES = ["Polygon", "MultiPolygon"]


def check_and_filter_shapefile(shp_path, filter_dict, output_path=None):
    # Open the Shapefile
    gdf = gpd.read_file(shp_path)

    geom_types = gdf.geometry.geom_type.unique()

    for geom_type in geom_types:
        if geom_type not in VALID_GEOM_TYPES:
            raise InvalidBoundaryGeomType(
                f"Invalid shapefile geom type. Expected one of {VALID_GEOM_TYPES}. Not {geom_type}")

    shp_fields = list(gdf.columns)
    required_fields = BOUNDARY_FIELDS.keys()

    for col in required_fields:
        if col not in shp_fields:
            raise MissingBoundaryField(
                f"The shapefile does not contain all the required fields. "
                f"The following fields must be present: {','.join(required_fields)} ")

    # Filter the data based on the filter dictionary
    for field, value in filter_dict.items():
        gdf = gdf[gdf[field] == value]

    if gdf.empty:
        raise NoMatchingBoundaryData(
            "No matching boundary data. "
            "Please check the selected country and make sure it exists in the provided shapefile")

    if output_path:
        # Save the filtered data to a new Shapefile
        gdf.to_file(output_path, driver='ESRI Shapefile')


def load_country_boundary(shp_zip_path, country_iso, remove_existing=True):
    boundary_filter = {"gid_0": country_iso}

    with tempfile.TemporaryDirectory() as tmpdir:
        shp = extract_zipped_shapefile(shp_zip_path, tmpdir)
        temp_shapefile_path = os.path.join(tmpdir, 'filtered_shapefile.shp')

        check_and_filter_shapefile(shp, boundary_filter, temp_shapefile_path)

        if remove_existing:
            # Delete all existing
            CountryBoundary.objects.all().delete()

        lm = LayerMapping(CountryBoundary, temp_shapefile_path, LAYER_MAPPING_FIELDS)
        lm.save(verbose=True)
