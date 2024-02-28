import os
import tempfile

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext as _
from wagtail.admin.forms import WagtailAdminModelForm

from geomanager.errors import InvalidGeomType, GeomValidationNotImplemented
from geomanager.models import AdditionalMapBoundaryData
from geomanager.settings import geomanager_settings
from geomanager.utils.vector_utils import ogr_db_import


class AdditionalBoundaryDataAddForm(WagtailAdminModelForm):
    file = forms.FileField(required=True,
                           label=_("Boundary Data"),
                           help_text=_(
                               "Upload a file containing the boundary data. "
                               "The file should be in Shapefile or GeoJSON format."),
                           )

    class Meta:
        model = AdditionalMapBoundaryData
        fields = ["name", "file", "render_layers"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # only accept zipped shapefiles and geojson files
        self.fields["file"].widget.attrs["accept"] = ".zip,.geojson"

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        name = cleaned_data.get("name")
        # slugify and replace dash with underscore
        table_name = slugify(name).replace("-", "_")

        if file:
            _, ext = os.path.splitext(file.name)

            with tempfile.NamedTemporaryFile(suffix=".upload" + ext) as temp_file:
                temp_file.write(file.read())
                temp_file.flush()

                default_db_settings = settings.DATABASES['default']

                db_params = {
                    "host": default_db_settings.get("HOST"),
                    "port": default_db_settings.get("PORT"),
                    "user": default_db_settings.get("USER"),
                    "password": default_db_settings.get("PASSWORD"),
                    "name": default_db_settings.get("NAME"),
                }

                db_settings = {
                    **db_params,
                    "pg_service_schema": geomanager_settings.get("vector_db_schema")
                }

                try:
                    table_info = ogr_db_import(temp_file.name, table_name, db_settings,
                                               validate_geom_types=["Polygon", "MultiPolygon"],
                                               overwrite=True)
                    cleaned_data["table_name"] = table_name
                    cleaned_data["properties"] = table_info.get("properties")
                    cleaned_data["geometry_type"] = table_info.get("geom_type")
                    cleaned_data["bounds"] = table_info.get("bounds")

                except (InvalidGeomType, GeomValidationNotImplemented) as e:
                    raise ValidationError(e)
                except Exception as e:
                    raise ValidationError(e)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Save the table name and properties
        instance.table_name = self.cleaned_data["table_name"]
        instance.properties = self.cleaned_data["properties"]
        instance.bounds = self.cleaned_data["bounds"]
        instance.geometry_type = self.cleaned_data["geometry_type"]

        if commit:
            instance.save()
        return instance


class AdditionalBoundaryDataEditForm(WagtailAdminModelForm):
    class Meta:
        model = AdditionalMapBoundaryData
        fields = ["name", "active", "render_layers"]
