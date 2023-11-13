import json
import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, close_old_connections
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.defaultfilters import filesizeformat
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission, permission_denied
from wagtail.api.v2.utils import get_full_url
from wagtail.models import Site
from wagtail.snippets.permissions import get_permission_name
from wagtail_modeladmin.helpers import AdminURLHelper
from wagtailcache.cache import cache_page, clear_cache

from geomanager.decorators import revalidate_cache
from geomanager.forms import VectorLayerFileForm, VectorTableForm
from geomanager.models import Dataset
from geomanager.models.core import GeomanagerSettings, Category
from geomanager.models.geostore import Geostore
from geomanager.models.vector_file import VectorUpload, PgVectorTable, VectorFileLayer, VectorLayerIcon
from geomanager.serializers.vector_file import VectorFileLayerSerializer
from geomanager.settings import geomanager_settings
from geomanager.utils import UUIDEncoder
from geomanager.utils.vector_utils import ogr_db_import

ALLOWED_VECTOR_EXTENSIONS = ["zip", "geojson", "csv"]


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

        query_set = VectorFileLayer.objects.filter(dataset=dataset)

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
            "geomanager/vector_file/vector_file_edit_form.html",
            ctx,
            request=request,
        )
        response.update({"form": form})

        return JsonResponse(response)

    return render(request, 'geomanager/vector_file/vector_file_upload.html', context)


@user_passes_test(user_has_any_page_permission)
def publish_vector(request, upload_id):
    if request.method != 'POST':
        return JsonResponse({"message": _("Only POST allowed")})

    upload = VectorUpload.objects.get(pk=upload_id)

    if not upload:
        return JsonResponse({"message": "upload not found"}, status=404)

    db_layer = get_object_or_404(VectorFileLayer, pk=request.POST.get('layer'))

    form_kwargs = {}

    data = {
        "layer": db_layer,
        "time": request.POST.get('time'),
        "table_name": request.POST.get('table_name'),
        "description": request.POST.get('description'),
    }

    queryset = VectorFileLayer.objects.filter(dataset=upload.dataset)
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
                "geomanager/vector_file/vector_file_edit_form.html",
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
            error_message = _("File with date %(time)s already exists for selected layer") % {"time": time.isoformat()}
            layer_form.add_error("time", error_message)
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
        return JsonResponse({"message": _("Only POST allowed")})

    upload = VectorUpload.objects.filter(pk=upload_id)

    if upload.exists():
        upload.first().delete()
    else:
        return JsonResponse({"success": True})
    return JsonResponse({"success": True, })


@user_passes_test(user_has_any_page_permission)
def preview_vector_layers(request, dataset_id, layer_id=None):
    template_name = 'geomanager/vector_file/vector_file_layer_preview.html'
    dataset = get_object_or_404(Dataset, pk=dataset_id)

    category_admin_helper = AdminURLHelper(Category)
    categories_url = category_admin_helper.get_action_url("index")

    dataset_admin_helper = AdminURLHelper(Dataset)
    dataset_list_url = dataset_admin_helper.get_action_url("index") + f"?id={dataset_id}"

    vector_layer_admin_helper = AdminURLHelper(VectorFileLayer)
    vector_layer_list_url = vector_layer_admin_helper.get_action_url("index")
    vector_layer_list_url = vector_layer_list_url + f"?dataset__id__exact={dataset_id}"

    geojson_url = get_full_url(request, reverse("feature_serv", args=("table_name",)).replace("table_name.geojson", ""))

    data_table = PgVectorTable.objects.filter(layer__id=layer_id)

    if data_table.exists():
        data_table = data_table.first()
    else:
        data_table = None

    initial_data = {
        "columns": data_table.properties if data_table else [],
    }

    dataset_layers = VectorFileLayerSerializer(dataset.vector_file_layers, many=True, context={"request": request}).data

    # get icon images for the dataset vector tile layers, if any
    icon_images = []
    layers_id = [layer.get("id") for layer in dataset_layers]
    for icon in VectorLayerIcon.objects.filter(layer__in=layers_id):
        icon_images.append({"name": icon.name, "url": get_full_url(request, icon.file.url)})

    navigation_items = [
        {"url": categories_url, "label": Category._meta.verbose_name_plural},
        {"url": dataset_list_url, "label": Dataset._meta.verbose_name_plural},
        {"url": vector_layer_list_url, "label": VectorFileLayer._meta.verbose_name_plural},
        {"url": "#", "label": _("Preview")},
    ]

    vector_tiles_url = reverse("vector_tiles", args=(0, 0, 0))
    vector_tiles_url = vector_tiles_url.replace("/0/0/0", r"/{z}/{x}/{y}")
    vector_tiles_url = get_full_url(request, vector_tiles_url)

    context = {
        "dataset": dataset,
        "dataset_layers": json.dumps(dataset_layers, cls=UUIDEncoder),
        "selected_layer": layer_id,
        "datasets_index_url": dataset_list_url,
        "vector_layer_list_url": vector_layer_list_url,
        "data_vector_api_base_url": get_full_url(request, reverse("vector-data-list")),
        "vector_tiles_url": vector_tiles_url,
        "geojson_url": geojson_url,
        "data_table": data_table,
        "icon_images": icon_images,
        "navigation_items": navigation_items,
    }

    if request.POST:
        form = VectorTableForm(request.POST, initial=initial_data)
        if form.is_valid():
            columns = form.cleaned_data.get("columns")

            if columns and data_table:
                data_table.properties = columns
                data_table.save()
                # clear wagtail cache
                clear_cache()
            messages.success(request, _("Data fields updated successfully"))
            # redirect
            return redirect(reverse("geomanager_preview_vector_layer", args=(dataset_id, layer_id)))
        else:
            context.update({"form": form})
            return render(request, template_name=template_name, context=context)
    else:
        form = VectorTableForm(initial=initial_data)
        context.update({"form": form})

    return render(request, template_name=template_name, context=context)


@method_decorator(revalidate_cache, name='get')
@method_decorator(cache_page, name='get')
class VectorTileView(View):
    def get(self, request, z, x, y):
        table_name = request.GET.get("table_name")
        geostore_id = request.GET.get("geostore_id")
        geostore = None

        if not table_name:
            return HttpResponse("Missing 'table_name' query parameter", status=400)

        try:
            vector_table = PgVectorTable.objects.get(table_name=table_name)
            # create list of columns to include in the vector tiles
            columns_sql = ", ".join(vector_table.columns) if vector_table.columns else "*"
        except ObjectDoesNotExist:
            return HttpResponse(f"Table matching 'table_name': {table_name} not found", status=404)

        if geostore_id:
            try:
                geostore = Geostore.objects.get(pk=geostore_id)
            except ObjectDoesNotExist:
                return HttpResponse(f"Geostore matching 'id': {geostore_id} not found", status=404)

            sql = f"""WITH
                        bounds AS (
                          SELECT ST_TileEnvelope(%s, %s, %s) AS geom
                        ),
                        clip_feature AS (
                            SELECT ST_GeomFromText(%s, 4326) AS geom
                        ),
                        mvtgeom AS (
                          SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                            {columns_sql}
                          FROM {vector_table.full_table_name} t, bounds, clip_feature
                          WHERE ST_Intersects(ST_Transform(t.geom, 4326), ST_Transform(bounds.geom, 4326))
                          AND ST_Intersects(t.geom, clip_feature.geom) 
                        )
                        SELECT ST_AsMVT(mvtgeom, 'default') FROM mvtgeom;
                        """
        else:
            sql = f"""WITH
                        bounds AS (
                          SELECT ST_TileEnvelope(%s, %s, %s) AS geom
                        ),
                        mvtgeom AS (
                          SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                            {columns_sql}
                          FROM {vector_table.full_table_name} t, bounds
                          WHERE ST_Intersects(ST_Transform(t.geom, 4326), ST_Transform(bounds.geom, 4326))
                        )
                        SELECT ST_AsMVT(mvtgeom, 'default') FROM mvtgeom;
                        """

        close_old_connections()
        with connection.cursor() as cursor:
            try:
                if geostore:
                    cursor.execute(sql, (z, x, y, geostore.geom.wkt))
                else:
                    cursor.execute(sql, (z, x, y))

                tile = cursor.fetchone()[0]
                if not tile:
                    return HttpResponse("Tile not found", status=404)
                return HttpResponse(tile, content_type="application/x-protobuf")
            except Exception as e:
                return HttpResponse(f"Error while fetching tile: {e}", status=500)


@method_decorator(revalidate_cache, name='get')
@method_decorator(cache_page, name='get')
class GeoJSONPgTableView(View):
    def get(self, request, table_name):
        try:
            vector_table = PgVectorTable.objects.get(table_name=table_name)
        except ObjectDoesNotExist:
            return JsonResponse({"message": f"Table with name: '{table_name}' does not exist"}, status=404)

        property_fields = ", ".join(vector_table.columns) if vector_table.columns else "*"

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
