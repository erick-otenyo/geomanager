from django_filters.rest_framework import DjangoFilterBackend
from django_large_image.rest import LargeImageFileDetailMixin
from rest_framework import mixins, viewsets

from geomanager.models import LayerRasterFile
from geomanager.serializers.raster_file import LayerRasterFileSerializer


class RasterLayerRasterFileDetailViewSet(mixins.ListModelMixin, viewsets.GenericViewSet, LargeImageFileDetailMixin, ):
    queryset = LayerRasterFile.objects.all()
    serializer_class = LayerRasterFileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["layer"]

    FILE_FIELD_NAME = "file"
