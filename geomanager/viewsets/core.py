from adminboundarymanager.models import AdminBoundarySettings
from rest_framework import mixins, viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from wagtail import hooks

from geomanager import serializers
from geomanager.models import Dataset
from geomanager.models.core import Metadata

geomanager_register_datasets_hook_name = "register_geomanager_datasets"


class DatasetViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Dataset.objects.filter(published=True)
    serializer_class = serializers.DatasetSerializer

    renderer_classes = [JSONRenderer]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        dataset_with_layers = []

        # get only datasets with layers defined
        for dataset in queryset:
            if dataset.has_layers():
                dataset_with_layers.append(dataset)

        serializer = self.get_serializer(dataset_with_layers, many=True)

        abm_settings = AdminBoundarySettings.for_request(request)
        datasets = serializer.data
        config = {}

        # set boundaries url. This will be used to create base boundary layer
        boundary_tiles_url = abm_settings.boundary_tiles_url
        boundary_tiles_url = request.scheme + '://' + request.get_host() + boundary_tiles_url
        config.update({"boundaryTilesUrl": boundary_tiles_url})

        for fn in hooks.get_hooks(geomanager_register_datasets_hook_name):
            hook_datasets = fn(request)
            for dataset in hook_datasets:
                datasets.append(dataset)

        return Response({"datasets": datasets, "config": config})


class MetadataViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Metadata.objects.all()
    serializer_class = serializers.MetadataSerialiazer
