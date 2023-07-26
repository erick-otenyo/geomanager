import tempfile

from django.conf import settings
from django.db import connection, close_old_connections
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission
from wagtailcache.cache import clear_cache, cache_page

from geomanager.forms import StationsUploadForm, StationColumnsForm
from geomanager.models import StationSettings
from geomanager.utils.vector_utils import ogr_db_import


@user_passes_test(user_has_any_page_permission)
def load_stations(request):
    template = "geomanager/stations_upload.html"

    context = {}
    station_settings = StationSettings.for_request(request)

    if request.POST:
        form = StationsUploadForm(request.POST, request.FILES)

        if form.is_valid():
            shp_zip = form.cleaned_data.get("shp_zip")

            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{shp_zip.name}") as temp_file:
                for chunk in shp_zip.chunks():
                    temp_file.write(chunk)

                try:
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
                        "pg_service_schema": station_settings.db_schema
                    }

                    table_info = ogr_db_import(temp_file.name, station_settings.stations_table_name, db_settings,
                                               overwrite=True, validate_geom_types=["Point", "MultiPoint"])

                    columns = table_info.get("properties")
                    geom_type = table_info.get("geom_type")
                    bounds = table_info.get("bounds")

                    # set all columns to show in table and popup
                    for column in columns:
                        column["table"] = False
                        column["popup"] = True

                        # set label to be the name by default
                        column["label"] = column.get("name")

                    # update stations settings
                    station_settings.columns = columns
                    station_settings.geom_type = geom_type
                    station_settings.bounds = bounds
                    station_settings.name_column = ""
                    station_settings.save()

                except Exception as e:
                    form.add_error(None, str(e))
                    context.update({"form": form})
                    return render(request, template_name=template, context=context)

            messages.success(request, "Stations data loaded successfully")

            # clear wagtail cache
            clear_cache()

            return redirect(reverse("geomanager_preview_stations"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        form = StationsUploadForm()
        context["form"] = form
        return render(request, template_name=template, context=context)


@user_passes_test(user_has_any_page_permission)
def preview_stations(request):
    template = "geomanager/stations_preview.html"

    stations_settings = StationSettings.for_request(request)
    stations_vector_tiles_url = request.scheme + '://' + request.get_host() + \
                                stations_settings.stations_vector_tiles_url

    context = {
        "mapConfig": {
            "stationBounds": stations_settings.bounds,
            "stationsVectorTilesUrl": stations_vector_tiles_url,
        },
        "load_stations_url": reverse("geomanager_load_stations"),
    }

    if stations_settings.columns:
        context.update({"station_columns": stations_settings.columns})

    initial_data = {
        "columns": stations_settings.columns,
        "name_column": stations_settings.name_column
    }

    column_choices = [(column, column) for column in stations_settings.station_columns_list]

    if request.POST:
        form = StationColumnsForm(request.POST, initial=initial_data, column_choices=column_choices)
        if form.is_valid():
            columns = form.cleaned_data.get("columns")
            name_column = form.cleaned_data.get("name_column")

            if columns:
                stations_settings.columns = columns
                stations_settings.name_column = name_column
                stations_settings.save()
                # clear wagtail cache
                clear_cache()
            messages.success(request, "Stations columns updated successfully")

            # redirect
            return redirect(reverse("geomanager_preview_stations"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        form = StationColumnsForm(initial=initial_data, column_choices=column_choices)
        context["form"] = form

    return render(request, template, context=context)


@method_decorator(cache_page, name='get')
class StationsTileView(View):
    def get(self, request, z, x, y):
        station_settings = StationSettings.for_request(request)

        sql = f"""WITH
            bounds AS (
              SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            ),
            mvtgeom AS (
              SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                *
              FROM {station_settings.full_table_name} t, bounds
              WHERE ST_Intersects(ST_Transform(t.geom, 4326), ST_Transform(bounds.geom, 4326))
            )
            SELECT ST_AsMVT(mvtgeom, 'default') FROM mvtgeom;
            """

        close_old_connections()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            tile = cursor.fetchone()[0]
            if not len(tile):
                raise Http404()

        return HttpResponse(tile, content_type="application/x-protobuf")
