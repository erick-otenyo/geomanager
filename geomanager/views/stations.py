import tempfile

from adminboundarymanager.models import AdminBoundarySettings
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission
from wagtailcache.cache import clear_cache

from geomanager.forms import StationsUploadForm
from geomanager.models import StationSettings
from geomanager.settings import geomanager_settings
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
                        "pg_service_schema": geomanager_settings.get("vector_db_schema")
                    }

                    table_info = ogr_db_import(temp_file.name, station_settings.stations_table_name, db_settings,
                                               overwrite=True, validate_geom_types=["Point", "MultiPoint"])

                    columns = table_info.get("properties")
                    geom_type = table_info.get("geom_type")
                    bounds = table_info.get("bounds")

                    # update stations settings
                    station_settings.columns = columns
                    station_settings.geom_type = geom_type
                    station_settings.bounds = bounds
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

    abm_settings = AdminBoundarySettings.for_request(request)
    stations_settings = StationSettings.for_request(request)
    stations_vector_tiles_url = request.scheme + '://' + request.get_host() + \
                                stations_settings.stations_vector_tiles_url

    context = {
        "mapConfig": {
            "combinedBbox": abm_settings.combined_countries_bounds,
            "stationsVectorTilesUrl": stations_vector_tiles_url,
            "columns": stations_settings.columns,
        },
        "load_stations_url": reverse("geomanager_load_stations"),
    }

    return render(request, template, context=context)
