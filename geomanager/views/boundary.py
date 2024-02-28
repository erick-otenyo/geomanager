from adminboundarymanager.models import AdminBoundarySettings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, close_old_connections
from django.http import HttpResponse
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
from geomanager.models import AdditionalMapBoundaryData


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

        close_old_connections()
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, (z, x, y))
                tile = cursor.fetchone()[0]
                if not tile:
                    return HttpResponse("Tile not found", status=404)
                return HttpResponse(tile, content_type="application/x-protobuf")
            except Exception as e:
                return HttpResponse(f"Error while fetching tile: {e}", status=500)
