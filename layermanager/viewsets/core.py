from rest_framework import mixins, viewsets
from rest_framework.response import Response

from layermanager import serializers
from layermanager.models import Dataset
from layermanager.models.core import LayerManagerSettings


class DatasetListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Dataset.objects.filter(public=True, published=True)
    serializer_class = serializers.DatasetSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        settings = LayerManagerSettings.for_request(request)
        datasets = serializer.data
        config = {}
        if settings.cap_base_url and settings.cap_sub_category:
            config.update({
                "capConfig": {
                    "initialVisible": settings.cap_shown_by_default,
                    "baseUrl": settings.cap_base_url,
                    "category": settings.cap_sub_category.category.pk,
                    "subCategory": settings.cap_sub_category.pk,
                    "refreshInterval": settings.cap_auto_refresh_interval_milliseconds
                }})

        return Response({"datasets": datasets, "config": config})
