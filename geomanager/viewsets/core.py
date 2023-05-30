from django.urls import reverse
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from geomanager import serializers
from geomanager.models import Dataset
from geomanager.models.core import GeomanagerSettings, Metadata


class DatasetListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Dataset.objects.filter(published=True)
    serializer_class = serializers.DatasetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        dataset_with_layers = []

        icons = []

        # get only datasets with layers defined
        for dataset in queryset:
            if dataset.has_layers():
                if dataset.layer_type == "vector":
                    vector_layers = dataset.vector_layers.all()
                    for layer in vector_layers:
                        layer_config = layer.layer_config()
                        render_layers = layer_config.get("render", {}).get("layers", [])
                        for render_layer in render_layers:
                            if render_layer.get("type", None) == "symbol":
                                icon_image = render_layer.get("layout", {}).get("icon-image")
                                icon_color = render_layer.get("paint", {}).get("icon-color")
                                if icon_image:
                                    icon = {"icon": icon_image, "type": "sprite"}
                                    if icon_color:
                                        icon.update({"icon-color": icon_color})
                                    icons.append(icon)

                dataset_with_layers.append(dataset)

        serializer = self.get_serializer(dataset_with_layers, many=True)

        lm_settings = GeomanagerSettings.for_request(request)
        datasets = serializer.data
        config = {}

        # set boundaries url. This will be used to create base boundary layer
        boundary_tiles_url = request.build_absolute_uri(reverse("boundary_tiles", args=(0, 0, 0)))
        boundary_tiles_url = boundary_tiles_url.replace("/0/0/0", r"/{z}/{x}/{y}")
        config.update({"boundaryTilesUrl": boundary_tiles_url})

        # set cap layer configuration. This will be used to create cap layer
        if lm_settings.cap_base_url and lm_settings.cap_sub_category:
            config.update({
                "capConfig": {
                    "initialVisible": lm_settings.cap_shown_by_default,
                    "baseUrl": lm_settings.cap_base_url,
                    "category": lm_settings.cap_sub_category.category.pk,
                    "subCategory": lm_settings.cap_sub_category.pk,
                    "refreshInterval": lm_settings.cap_auto_refresh_interval_milliseconds,
                    "metadata": lm_settings.cap_metadata.pk if lm_settings.cap_metadata else None
                }})

        return Response({"datasets": datasets, "config": config, "icons": icons})


class MetadataViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Metadata.objects.all()
    serializer_class = serializers.MetadataSerialiazer
