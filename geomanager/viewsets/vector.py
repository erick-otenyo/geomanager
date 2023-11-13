import json

from adminboundarymanager.models import AdminBoundary, AdminBoundarySettings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import MultiPolygon
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from wagtailcache.cache import cache_page

from geomanager import serializers
from geomanager.decorators import revalidate_cache
from geomanager.models import Geostore
from geomanager.models.vector_file import PgVectorTable
from geomanager.serializers.geostore import GeostoreSerializer
from geomanager.serializers.vector_file import AdminBoundarySerializer


class VectorTableFileDetailViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    renderer_classes = [JSONRenderer]
    queryset = PgVectorTable.objects.all()
    serializer_class = serializers.PgVectorTableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["layer"]


class AdminBoundaryViewSet(viewsets.ViewSet):
    renderer_classes = [JSONRenderer]

    @action(detail=True, methods=['get'])
    @method_decorator(revalidate_cache)
    @method_decorator(cache_page)
    def get(self, request):
        countries = AdminBoundary.objects.filter(level=0)
        data = AdminBoundarySerializer(countries, many=True).data
        return Response(data)

    @action(detail=True, methods=['get'])
    @method_decorator(revalidate_cache)
    @method_decorator(cache_page)
    def get_regions(self, request, gid_0):
        countries = AdminBoundary.objects.filter(level=1, gid_0=gid_0)
        data = AdminBoundarySerializer(countries, many=True).data
        return Response(data)

    @action(detail=True, methods=['get'])
    @method_decorator(revalidate_cache)
    @method_decorator(cache_page)
    def get_sub_regions(self, request, gid_0, gid_1):
        countries = AdminBoundary.objects.filter(level=2, gid_0=gid_0, gid_1=gid_1)
        data = AdminBoundarySerializer(countries, many=True).data
        return Response(data)


class GeostoreViewSet(viewsets.ViewSet):
    renderer_classes = [JSONRenderer]

    @action(detail=True, methods=['post'])
    def post(self, request):
        # parse the GeoJSON from the POST data
        payload = json.loads(request.body.decode('utf-8'))

        geojson = payload.get("geojson")

        # extract the MultiPolygon geometry from the GeoJSON
        geometry = geojson['geometry']
        geom = GEOSGeometry(json.dumps(geometry))

        if geom.geom_type == "Polygon":
            geom = MultiPolygon(geom)

        # create a new Geostore object and save it to the database
        geostore = Geostore(geom=geom)
        geostore.save()

        res_data = GeostoreSerializer(geostore).data

        return Response(res_data)

    @action(detail=True, methods=['get'])
    @method_decorator(revalidate_cache)
    @method_decorator(cache_page)
    def get(self, request, geostore_id):
        try:
            geostore = Geostore.objects.get(id=geostore_id)
            res_data = GeostoreSerializer(geostore).data
            return Response(res_data)
        except Geostore.DoesNotExist:
            raise NotFound(detail='Geostore not found')

    @action(detail=True, methods=['get'])
    @method_decorator(revalidate_cache)
    @method_decorator(cache_page)
    def get_by_admin(self, request, gid_0, gid_1=None, gid_2=None):
        abm_settings = AdminBoundarySettings.for_request(request)
        data_source = abm_settings.data_source

        simplify_thresh = request.GET.get("thresh")

        geostore_filter = {
            "iso": gid_0,
            "id1": None,
            "id2": None,
        }

        boundary_filter = {
            "gid_0": gid_0,
            "level": 0
        }

        if data_source != "gadm41":
            if gid_1:
                geostore_filter.update({"id1": gid_1})
                boundary_filter.update({"gid_1": gid_1, "level": 1})
            if gid_2:
                geostore_filter.update({"id2": gid_2})
                boundary_filter.update({"gid_2": gid_2, "level": 2})
        else:
            if gid_1:
                geostore_filter.update({"id1": gid_1})
                boundary_filter.update({"gid_1": f"{gid_0}.{gid_1}_1", "level": 1})
            if gid_2:
                geostore_filter.update({"id2": gid_2})
                boundary_filter.update({"gid_2": f"{gid_0}.{gid_1}.{gid_2}_1", "level": 2})

        geostore = Geostore.objects.filter(**geostore_filter)
        should_save = False

        if not geostore.exists():
            should_save = True
            geostore = AdminBoundary.objects.filter(**boundary_filter)

        if not geostore.exists():
            raise NotFound(detail='Geostore not found')

        geostore = geostore.first()

        geom = geostore.geom

        if simplify_thresh:
            geom = geostore.geom.simplify(tolerance=float(simplify_thresh))

        # convert to multipolygon if not
        if geom.geom_type != "MultiPolygon":
            geom = MultiPolygon(geom)

        if should_save:
            geostore_data = {
                "iso": geostore.gid_0,
                "id1": gid_1,
                "id2": gid_2,
                "name_0": geostore.name_0,
                "name_1": geostore.name_1,
                "name_2": geostore.name_2,
                "geom": geom
            }

            geostore = Geostore.objects.create(**geostore_data)

        res_data = GeostoreSerializer(geostore).data

        return Response(res_data)
