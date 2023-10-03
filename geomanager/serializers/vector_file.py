from adminboundarymanager.models import AdminBoundary
from rest_framework import serializers

from geomanager.models.vector_file import (
    PgVectorTable,
    VectorFileLayer,
)


class AdminBoundarySerializer(serializers.ModelSerializer):
    bbox = serializers.ListField()

    class Meta:
        model = AdminBoundary
        fields = ("level", "name_0", "name_1", "name_2", "gid_0", "gid_1", "gid_2", "bbox")


class BoundsFieldSerializer(serializers.Field):
    def to_representation(self, value):
        # Convert the value of the custom field to a string for serialization
        return [float(value) for value in list(value)]


class PgVectorTableSerializer(serializers.ModelSerializer):
    bounds = BoundsFieldSerializer()

    class Meta:
        model = PgVectorTable
        fields = '__all__'


class VectorFileLayerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    layerConfig = serializers.SerializerMethodField()
    layerType = serializers.SerializerMethodField()
    params = serializers.SerializerMethodField()
    paramsSelectorConfig = serializers.SerializerMethodField()
    legendConfig = serializers.SerializerMethodField()
    multiTemporal = serializers.SerializerMethodField()
    currentTimeMethod = serializers.SerializerMethodField()
    autoUpdateInterval = serializers.SerializerMethodField()
    isMultiLayer = serializers.SerializerMethodField()
    nestedLegend = serializers.SerializerMethodField()
    interactionConfig = serializers.SerializerMethodField()
    canClip = serializers.SerializerMethodField()

    class Meta:
        model = VectorFileLayer
        fields = ["id", "dataset", "name", "layerType", "multiTemporal", "isMultiLayer", "legendConfig", "nestedLegend",
                  "layerConfig", "params", "paramsSelectorConfig", "currentTimeMethod", "autoUpdateInterval",
                  "interactionConfig", "canClip"]

    def get_isMultiLayer(self, obj):
        return obj.dataset.multi_layer

    def get_nestedLegend(self, obj):
        return obj.dataset.multi_layer

    def get_autoUpdateInterval(self, obj):
        return obj.dataset.auto_update_interval_milliseconds

    def get_multiTemporal(self, obj):
        return obj.dataset.multi_temporal

    def get_currentTimeMethod(self, obj):
        return obj.dataset.current_time_method

    def get_layerConfig(self, obj):
        request = self.context.get('request')

        layer_config = obj.layer_config(request)
        return layer_config

    def get_layerType(self, obj):
        return obj.dataset.layer_type

    def get_name(self, obj):
        return obj.title

    def get_params(self, obj):
        return obj.params

    def get_paramsSelectorConfig(self, obj):
        return obj.param_selector_config

    def get_paramsSelectorColumnView(self, obj):
        return not obj.params_selectors_side_by_side

    def get_legendConfig(self, obj):
        request = self.context.get('request')
        return obj.get_legend_config(request)

    def get_getCapabilitiesUrl(self, obj):
        return obj.get_capabilities_url

    def get_layerName(self, obj):
        return obj.layer_name

    def get_interactionConfig(self, obj):
        return obj.interaction_config

    def get_canClip(self, obj):
        return obj.dataset.can_clip
