import rasterio
import requests
from django_filters.rest_framework import DjangoFilterBackend
from django_large_image.rest import LargeImageFileDetailMixin, LargeImageDetailMixin
from django_large_image.utilities import make_vsi
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from geomanager import serializers
from geomanager.models import LayerRasterFile


class CustomLargeImageFileDetailMixin(LargeImageFileDetailMixin):
    @action(detail=True, url_path='data/pixel')
    def pixel(self, request: Request, pk: int = None, **kwargs) -> Response:
        x_coord = float(self.get_query_param(request, 'x'))
        y_coord = float(self.get_query_param(request, 'y'))
        source = self.get_tile_source(request, pk)

        # get raster gdal geotransform
        gdal_geot = source.getInternalMetadata().get("GeoTransform")
        transform = rasterio.Affine.from_gdal(*gdal_geot)

        # get corresponding row col
        row_col = rasterio.transform.rowcol(transform, xs=x_coord, ys=y_coord)
        metadata = source.getPixel(region={'left': abs(row_col[1]), 'top': abs(row_col[0])})

        return Response(metadata)


class FileImageLayerRasterFileDetailViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
    CustomLargeImageFileDetailMixin,
):
    queryset = LayerRasterFile.objects.all()
    serializer_class = serializers.FileImageLayerRasterFileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["layer"]

    FILE_FIELD_NAME = "file"


class URLLargeImageViewMixin(LargeImageDetailMixin):
    def get_path(self, request, pk):
        t = request.GET.get("time")
        obj = self.get_object()

        if not t:
            raise ValidationError("Missing time query parameter")

        file_base_url = obj.file_base_url
        file_name_template = obj.file_name_template
        timestamps_url = obj.timestamps_url
        timestamps_data_key = obj.timestamps_data_key

        r = requests.get(timestamps_url)
        timestamps = r.json()

        if timestamps:
            if timestamps_data_key and timestamps.get(timestamps_data_key):
                timestamps = timestamps.get(timestamps_data_key)

        if t not in timestamps:
            raise ValidationError("time not found in available times")

        file_url = f"{file_base_url}/{file_name_template.replace('{time}', t)}"

        return make_vsi(file_url)
