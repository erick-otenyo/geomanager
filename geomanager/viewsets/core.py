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

        datasets = []

        # get datasets from registered hooks
        for fn in hooks.get_hooks(geomanager_register_datasets_hook_name):
            hook_datasets = fn(request)
            if isinstance(hook_datasets, list):
                for dataset in hook_datasets:
                    datasets.append(dataset)

        # get only datasets with layers defined
        for dataset in queryset:
            if dataset.has_layers():
                # if dataset requires file upload, but has no files, skip
                if dataset.requires_file_upload and not dataset.has_files:
                    continue
                dataset_with_layers.append(dataset)

        serializer = self.get_serializer(dataset_with_layers, many=True)
        geomanager_datasets = serializer.data

        if geomanager_datasets:
            datasets.extend(geomanager_datasets)

        return Response(datasets)

class DatasetSlugViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Dataset.objects.exclude(dataset_slug=None)
    serializer_class = serializers.DatasetSerializer
    lookup_field = "dataset_slug"
    renderer_classes = [JSONRenderer]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)
    
class MetadataViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Metadata.objects.all()
    serializer_class = serializers.MetadataSerialiazer
