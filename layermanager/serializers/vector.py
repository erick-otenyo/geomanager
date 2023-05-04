from rest_framework import serializers

from layermanager.models.vector import (
    PgVectorTable,
    VectorLayer,
    CountryBoundary, Geostore
)
from layermanager.utils.vector_utils import create_feature_collection_from_geom


class CountrySerializer(serializers.ModelSerializer):
    bbox = serializers.ListField()

    class Meta:
        model = CountryBoundary
        fields = ("level", "name_0", "name_1", "name_2", "gid_0", "gid_1", "gid_2", "size", "bbox")


class BoundsFieldSerializer(serializers.Field):
    def to_representation(self, value):
        # Convert the value of the custom field to a string for serialization
        return [float(value) for value in list(value)]


class PgVectorTableSerializer(serializers.ModelSerializer):
    bounds = BoundsFieldSerializer()

    class Meta:
        model = PgVectorTable
        fields = '__all__'


class VectorLayerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    layerConfig = serializers.SerializerMethodField()
    layerType = serializers.SerializerMethodField()

    class Meta:
        model = VectorLayer
        fields = ["id", "dataset", "layerType", "name", "layerConfig"]

    def get_layerType(self, obj):
        return obj.dataset.layer_type

    def get_name(self, obj):
        return obj.title

    def get_layerConfig(self, obj):
        request = self.context.get('request')
        layer_config = obj.layer_config(request)
        return layer_config


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
