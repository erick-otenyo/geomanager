from rest_framework import serializers

from geomanager.models.geostore import Geostore
from geomanager.utils.vector_utils import create_feature_collection_from_geom


class GeostoreSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Geostore
        fields = ["id", "attributes"]

    def get_attributes(self, obj):
        geostore = {
            'info': obj.info,
            'geojson': create_feature_collection_from_geom(obj.geom),
            'bbox': obj.bbox,
            'hash': obj.pk
        }

        return geostore
