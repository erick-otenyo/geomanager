import json

from adminboundarymanager.models import AdminBoundarySettings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from wagtail.admin.views.generic import (
    IndexView,
    CreateView,
    EditView,
    DeleteView
)

from geomanager.forms.boundary import AdditionalBoundaryDataAddForm, AdditionalBoundaryDataEditForm
from geomanager.models import AdditionalMapBoundaryData, Geostore
from geomanager.serializers.geostore import GeostoreSerializer


def boundary_landing_view(request, ):
    links = []
    try:
        settings_url = reverse(
            "wagtailsettings:edit",
            args=[AdminBoundarySettings._meta.app_label, AdminBoundarySettings._meta.model_name, ],
        )
        links.append({
            "url": settings_url,
            "icon": "cog",
            "title": _("Boundary Settings"),
        })

        preview_url = reverse("adminboundarymanager_preview_boundary")

        links.append({
            "url": preview_url,
            "icon": "upload",
            "title": _("Country Boundary Loader"),
        })
    except Exception:
        pass

    links.append({
        "url": reverse("additional_boundary_index"),
        "icon": "layer-group",
        "title": _("Additional Map Boundaries"),
    })

    context = {
        "links": links,
    }

    return render(request, "geomanager/boundary/boundary_landing.html", context)


class AdditionalBoundaryIndexView(IndexView):
    model = AdditionalMapBoundaryData
    add_url_name = "additional_boundary_create"
    edit_url_name = "additional_boundary_edit"
    delete_url_name = "additional_boundary_delete"


class AdditionalBoundaryCreateView(CreateView):
    model = AdditionalMapBoundaryData
    form_class = AdditionalBoundaryDataAddForm
    index_url_name = "additional_boundary_index"
    add_url_name = "additional_boundary_create"
    edit_url_name = "additional_boundary_edit"
    success_message = _("Boundary dataset '%(object)s' created.")


class AdditionalBoundaryEditView(EditView):
    model = AdditionalMapBoundaryData
    form_class = AdditionalBoundaryDataEditForm
    edit_url_name = "additional_boundary_edit"
    index_url_name = "additional_boundary_index"


class AdditionalBoundaryDeleteView(DeleteView):
    model = AdditionalMapBoundaryData
    index_url_name = "additional_boundary_index"
    delete_url_name = "additional_boundary_delete"

    success_message = _("Boundary dataset '%(object)s' deleted.")


class AdditionalBoundaryVectorTileView(View):
    def get(self, request, table_name, z, x, y):
        try:
            vector_table = AdditionalMapBoundaryData.objects.get(table_name=table_name)
            # create list of columns to include in the vector tiles
            columns_sql = ", ".join(vector_table.columns) if vector_table.columns else "*"
        except ObjectDoesNotExist:
            return HttpResponse(f"Table matching 'table_name': {table_name} not found", status=404)

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

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, (z, x, y))
                tile = cursor.fetchone()[0]
                if not tile:
                    return HttpResponse("Tile not found", status=404)
                return HttpResponse(tile, content_type="application/x-protobuf")
            except Exception as e:
                return HttpResponse(f"Error while fetching tile: {e}", status=500)


def get_boundary_data_feature_by_id(request, table_name, gid):
    identifier = f"{table_name}-{gid}"

    try:
        vector_table = AdditionalMapBoundaryData.objects.get(table_name=table_name)
    except ObjectDoesNotExist:
        return JsonResponse({"message": f"Table with name: '{table_name}' does not exist"}, status=404)

    geostore = Geostore.objects.filter(iso=identifier).first()
    if geostore:
        res_data = GeostoreSerializer(geostore).data
        return JsonResponse(res_data)

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
                    SELECT gid, geom
                    FROM {vector_table.full_table_name}
                    WHERE gid={gid}
                ) AS inputs
            ) AS features;
        """

        cursor.execute(query)
        data = cursor.fetchone()[0]

    if data.get("features") is None:
        return JsonResponse({"message": "Not Found"}, status=404)

    feature = data.get("features")[0]
    geom = GEOSGeometry(json.dumps(feature.get("geometry")))

    if geom.geom_type == "Polygon":
        geom = MultiPolygon(geom)

    # create a new Geostore object and save it to the database
    geostore = Geostore(geom=geom, iso=identifier)
    geostore.save()

    res_data = GeostoreSerializer(geostore).data

    return JsonResponse(res_data)
