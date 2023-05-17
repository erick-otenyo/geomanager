import requests
from django_filters.rest_framework import DjangoFilterBackend
from django_large_image.rest import LargeImageFileDetailMixin, LargeImageDetailMixin
from django_large_image.utilities import make_vsi
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from geomanager import serializers
from geomanager.models import LayerRasterFile


class FileImageLayerRasterFileDetailViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
    LargeImageFileDetailMixin,
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
