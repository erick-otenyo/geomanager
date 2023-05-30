import os
import tempfile

import fiona
import geopandas as gpd
from django.contrib.gis.utils import LayerMapping

from geomanager.errors import MissingBoundaryField, NoMatchingBoundaryData, InvalidBoundaryGeomType, \
    NoMatchingBoundaryLayer
from geomanager.models.vector import CountryBoundary
from django.db import transaction

BOUNDARY_FIELDS = {
    "name_0": "COUNTRY",
    "name_1": "NAME_1",
    "name_2": "NAME_2",
    "gid_0": "GID_0",
    "gid_1": "GID_1",
    "gid_2": "GID_2",
    "level": "LEVEL",
}

LAYER_MAPPING_FIELDS = {
    **BOUNDARY_FIELDS,
    "geom": "MULTIPOLYGON",
}

VALID_GEOM_TYPES = ["Polygon", "MultiPolygon"]

LEVELS = [0, 1, 2, 3]


@transaction.atomic
def check_and_load_boundaries(geopackage_path, country_iso, gadm_version=4.1):
    layers = fiona.listlayers(geopackage_path)

    layers_name_prefix = f"ADM_ADM_"

    found_level_layers = []
    for level in LEVELS:
        layer_name = layers_name_prefix + str(level)
        if layer_name in layers:
            found_level_layers.append({"layer_name": layer_name, "level": level})

    if not found_level_layers:
        raise NoMatchingBoundaryLayer(f"No Matching layers in geopackage for version {gadm_version}. "
                                      f"Please make sure you have downloaded the correct version. "
                                      f"The expected version is {gadm_version} and the "
                                      f"country iso set is {country_iso}")

    # Delete existing
    CountryBoundary.objects.all().delete()

    for layer in found_level_layers:
        level = layer.get("level")
        layer_name = layer.get("layer_name")

        # read geopackage
        gdf = gpd.read_file(geopackage_path, layer=layer_name)

        # assign level
        gdf = gdf.assign(LEVEL=level)

        if level == 0:
            gdf = gdf.assign(GID_1=None)
            gdf = gdf.assign(GID_2=None)
            gdf = gdf.assign(NAME_1=None)
            gdf = gdf.assign(NAME_2=None)

        if level == 1:
            gdf = gdf.assign(GID_2=None)
            gdf = gdf.assign(NAME_2=None)

        geom_types = gdf.geometry.geom_type.unique()

        for geom_type in geom_types:
            if geom_type not in VALID_GEOM_TYPES:
                raise InvalidBoundaryGeomType(
                    f"Invalid geometry type. Expected one of {VALID_GEOM_TYPES}. Not {geom_type}")

        layer_fields = list(gdf.columns)
        required_fields = BOUNDARY_FIELDS.values()

        for col in required_fields:
            if col not in layer_fields:
                raise MissingBoundaryField(
                    f"The geopackage does not contain all the required fields. "
                    f"The following fields must be present: {','.join(required_fields)} ")

        # Filter the data by country
        gdf = gdf[gdf["GID_0"] == country_iso]

        if gdf.empty:
            raise NoMatchingBoundaryData(
                "No matching boundary data. "
                "Please check the selected country and make sure it exists in the provided shapefile")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_shapefile_path = os.path.join(tmpdir, f'{layer_name}_shapefile.shp')
            # Save the filtered data to a new Shapefile
            gdf.to_file(temp_shapefile_path, driver='ESRI Shapefile')

            lm = LayerMapping(CountryBoundary, temp_shapefile_path, LAYER_MAPPING_FIELDS)
            lm.save()


def load_country_boundary(geopackage_path, country_iso, gadm_version, remove_existing=True):
    check_and_load_boundaries(geopackage_path, country_iso, gadm_version)
