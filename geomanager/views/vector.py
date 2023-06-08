import os
import tempfile

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, close_old_connections
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission, permission_denied
from wagtail.contrib.modeladmin.helpers import AdminURLHelper
from wagtail.models import Site
from wagtail.snippets.permissions import get_permission_name

from geomanager.forms import VectorLayerFileForm, BoundaryUploadForm
from geomanager.models import Dataset
from geomanager.models.core import GeomanagerSettings
from geomanager.models.vector import VectorLayer, VectorUpload, PgVectorTable, CountryBoundary
from geomanager.settings import geomanager_settings
from geomanager.utils.boundary_loader import load_country_boundary
from geomanager.utils.vector_utils import ogr_db_import

ALLOWED_VECTOR_EXTENSIONS = ["zip", "geojson", "csv"]


@user_passes_test(user_has_any_page_permission)
def load_boundary(request):
    template = "geomanager/boundary_loader.html"

    lm_settings = GeomanagerSettings.for_request(request)
    country = lm_settings.country
    gadm_version = lm_settings.gadm_version
    context = {"country": country}

    settings_url = reverse(
        "wagtailsettings:edit",
        args=[GeomanagerSettings._meta.app_label, GeomanagerSettings._meta.model_name, ],
    )

    context.update({"settings_url": settings_url})

    if request.POST:
        form = BoundaryUploadForm(request.POST, request.FILES)

        if form.is_valid():
            geopackage = form.cleaned_data.get("geopackage")
            remove_existing = form.cleaned_data.get("remove_existing")

            if not country:
                form.add_error(None, "Please select a country in layer manager settings and try again")

            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{geopackage.name}") as temp_file:
                for chunk in geopackage.chunks():
                    temp_file.write(chunk)

                try:
                    load_country_boundary(geopackage_path=temp_file.name,
                                          country_iso=country.alpha3,
                                          gadm_version=gadm_version,
                                          remove_existing=remove_existing)
                except Exception as e:
                    form.add_error(None, str(e))
                    context.update({"form": form, "has_error": True})
                    countries = CountryBoundary.objects.filter(level=0)

                    if countries.exists():
                        context.update({"existing_countries": countries})

                    return render(request, template_name=template, context=context)

            messages.success(request, "Boundary data loaded successfully")
            return redirect(reverse("wagtailadmin_home"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        countries = CountryBoundary.objects.filter(level=0)
        if countries.exists():
            context["existing_countries"] = countries

        form = BoundaryUploadForm()
        context["form"] = form

        return render(request, template_name=template, context=context)


@user_passes_test(user_has_any_page_permission)
def upload_vector_file(request, dataset_id=None, layer_id=None):
    permission = get_permission_name('change', Dataset)
    if not request.user.has_perm(permission):
        return permission_denied(request)

    site = Site.objects.get(is_default_site=True)
    layer_manager_settings = GeomanagerSettings.for_site(site)

    file_error_messages = {
        "invalid_file_extension": _(
            "Not a supported vector format. Supported formats: %(supported_formats)s."
        ) % {"supported_formats": ALLOWED_VECTOR_EXTENSIONS},
        "file_too_large": _(
            "This file is too big (%(file_size)s). Maximum filesize %(max_filesize)s."
        ),
        "file_too_large_unknown_size": _(
            "This file is too big. Maximum filesize %(max_filesize)s."
        ) % {"max_filesize": filesizeformat(layer_manager_settings.max_upload_size_bytes)}}

    layer = None
    context = {}
    context.update(
        {
            "max_filesize": layer_manager_settings.max_upload_size_bytes,
            "allowed_extensions": ALLOWED_VECTOR_EXTENSIONS,
            "error_max_file_size": file_error_messages["file_too_large_unknown_size"],
            "error_accepted_file_types": file_error_messages["invalid_file_extension"],
        }
    )

    dataset = get_object_or_404(Dataset, pk=dataset_id)

    admin_url_helper = AdminURLHelper(Dataset)
    dataset_list_url = admin_url_helper.get_action_url("index")
    layer_list_url = None
    layer_preview_url = None

    context.update({"dataset": dataset, "layer": layer, "datasets_index_url": dataset_list_url,
                    "layers_index_url": layer_list_url, "dataset_preview_url": dataset.preview_url,
                    "layer_preview_url": layer_preview_url})

    # Check if user is submitting
    if request.method == 'POST':
        files = request.FILES.getlist('files[]', None)
        file = files[0]

        upload = VectorUpload.objects.create(file=file, dataset=dataset)
        upload.save()

        query_set = VectorLayer.objects.filter(dataset=dataset)

        filename = os.path.splitext(upload.file.name)[0]
        filename_without_ext = os.path.basename(filename)

        initial_data = {
            "layer": layer_id if layer_id else query_set.first(),
            "table_name": filename_without_ext
        }

        form_kwargs = {}

        layer_form = VectorLayerFileForm(queryset=query_set, initial=initial_data, **form_kwargs)

        ctx = {
            "form": layer_form,
            "dataset": dataset,
            "publish_action": reverse("geomanager_publish_vector", args=[upload.pk]),
            "delete_action": reverse("geomanager_delete_vector_upload", args=[upload.pk]),
        }

        response = {
            "success": True,
        }

        form = render_to_string(
            "geomanager/vector_edit_form.html",
            ctx,
            request=request,
        )
        response.update({"form": form})

        return JsonResponse(response)

    return render(request, 'geomanager/vector_upload.html', context)


@user_passes_test(user_has_any_page_permission)
def publish_vector(request, upload_id):
    if request.method != 'POST':
        return JsonResponse({"message": "Only POST allowed"})

    upload = VectorUpload.objects.get(pk=upload_id)

    if not upload:
        return JsonResponse({"message": "upload not found"}, status=404)

    db_layer = get_object_or_404(VectorLayer, pk=request.POST.get('layer'))

    form_kwargs = {}

    data = {
        "layer": db_layer,
        "time": request.POST.get('time'),
        "table_name": request.POST.get('table_name'),
        "description": request.POST.get('description'),
    }

    queryset = VectorLayer.objects.filter(dataset=upload.dataset)
    layer_form = VectorLayerFileForm(data=data, queryset=queryset, **form_kwargs)

    ctx = {
        "dataset": upload.dataset,
        "publish_action": reverse("geomanager_publish_vector", args=[upload.pk]),
        "delete_action": reverse("geomanager_delete_vector_upload", args=[upload.pk]),
        "form": layer_form
    }

    def get_response():
        return {
            "success": False,
            "form": render_to_string(
                "geomanager/vector_edit_form.html",
                ctx,
                request=request,
            ),
        }

    if layer_form.is_valid():
        layer = layer_form.cleaned_data['layer']
        time = layer_form.cleaned_data['time']
        table_name = layer_form.cleaned_data['table_name']
        if table_name:
            table_name = table_name.lower()
        description = layer_form.cleaned_data['description']

        exists = PgVectorTable.objects.filter(layer=db_layer, time=time, table_name=table_name).exists()

        if exists:
            layer_form.add_error("time", f"File with date {time} already exists for selected layer")
            return JsonResponse(get_response())

        data = {
            "layer": layer,
            "time": time,
            "table_name": table_name,
            "description": description
        }

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

        table_info = ogr_db_import(upload.file.path, table_name, db_settings)
        full_table_name = table_info.get("table_name")
        properties = table_info.get("properties")
        bounds = table_info.get("bounds")
        geom_type = table_info.get("geom_type")

        data.update({
            "full_table_name": full_table_name,
            "properties": properties,
            "bounds": bounds,
            "geometry_type": geom_type
        })

        PgVectorTable.objects.create(**data)

        # cleanup
        upload.delete()
        return JsonResponse({"success": True, })
    else:
        return JsonResponse(get_response())


@user_passes_test(user_has_any_page_permission)
def delete_vector_upload(request, upload_id):
    if request.method != 'POST':
        return JsonResponse({"message": "Only POST allowed"})

    upload = VectorUpload.objects.filter(pk=upload_id)

    if upload.exists():
        upload.first().delete()
    else:
        return JsonResponse({"success": True})

    return JsonResponse({"success": True, })


@user_passes_test(user_has_any_page_permission)
def preview_vector_layers(request, dataset_id, layer_id=None):
    dataset = get_object_or_404(Dataset, pk=dataset_id)

    base_absolute_url = request.scheme + '://' + request.get_host()

    dataset_admin_helper = AdminURLHelper(Dataset)
    dataset_list_url = dataset_admin_helper.get_action_url("index")

    vector_layer_admin_helper = AdminURLHelper(VectorLayer)
    vector_layer_list_url = vector_layer_admin_helper.get_action_url("index")

    context = {
        "dataset": dataset,
        "selected_layer": layer_id,
        "datasets_index_url": dataset_list_url,
        "vector_layer_list_url": vector_layer_list_url,
        "data_vector_api_base_url": request.build_absolute_uri("/api/vector-data"),
        "vector_tiles_url": base_absolute_url + "/api/vector-tiles/{z}/{x}/{y}",
    }

    return render(request, 'geomanager/vector_preview.html', context)


class VectorTileView(View):
    def get(self, request, z, x, y):
        table_name = request.GET.get("table_name")

        if table_name is None:
            return HttpResponse("Missing table_name query parameter", status=400)

        vector_table = PgVectorTable.objects.filter(table_name=table_name)

        if not vector_table.exists():
            return HttpResponse(f"Table not found matching 'name': {table_name}",
                                status=404)

        if vector_table.exists():
            vector_table = vector_table.first()

        sql = f"""WITH
            bounds AS (
              SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            ),
            mvtgeom AS (
              SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                *
              FROM {vector_table.full_table_name} t, bounds
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


class BoundaryVectorTileView(View):
    def get(self, request, z, x, y):
        gid_0 = request.GET.get("gid_0")
        boundary_filter = ""
        if gid_0:
            boundary_filter = f"AND t.gid_0='{gid_0}'"

        sql = f"""WITH
            bounds AS (
              SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            ),
            mvtgeom AS (
              SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                *
              FROM geomanager_countryboundary t, bounds
              WHERE ST_Intersects(ST_Transform(t.geom, 4326), ST_Transform(bounds.geom, 4326)) {boundary_filter}
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


class GeoJSONPgTableView(View):
    def get(self, request, table_name):
        try:
            vector_table = PgVectorTable.objects.get(table_name=table_name)
        except ObjectDoesNotExist:
            return JsonResponse({"message": f"Table with name: '{table_name}' does not exist"}, status=404)

        table_columns = [prop.get("name") for prop in vector_table.properties]
        property_fields = ", ".join(table_columns) if table_columns else "*"

        close_old_connections()

        with connection.cursor() as cursor:
            query = f"""
                SELECT json_build_object(
                    'type', 'FeatureCollection', 
                    'features', json_agg(feature)
                ) FROM (
                    SELECT json_build_object(
                        'type', 'Feature', 
                        'geometry', ST_AsGeoJSON(geom)::json, 
                        'properties', to_jsonb(inputs) - 'geom'
                    ) AS feature 
                    FROM (
                        SELECT {property_fields}, geom
                        FROM {vector_table.full_table_name}
                    ) AS inputs
                ) AS features;
            """

            cursor.execute(query)
            data = cursor.fetchone()[0]

        return JsonResponse(data)
