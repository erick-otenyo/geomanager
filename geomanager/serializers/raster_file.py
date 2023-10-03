from rest_framework import serializers

from geomanager.models import LayerRasterFile, RasterFileLayer


class RasterFileLayerSerializer(serializers.ModelSerializer):
    layerConfig = serializers.SerializerMethodField()
    params = serializers.SerializerMethodField()
    paramsSelectorConfig = serializers.SerializerMethodField()
    legendConfig = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    layerType = serializers.SerializerMethodField()
    multiTemporal = serializers.SerializerMethodField()
    currentTimeMethod = serializers.SerializerMethodField()
    autoUpdateInterval = serializers.SerializerMethodField()
    isMultiLayer = serializers.SerializerMethodField()
    nestedLegend = serializers.SerializerMethodField()
    canClip = serializers.SerializerMethodField()
    analysisConfig = serializers.SerializerMethodField()
    tileJsonUrl = serializers.SerializerMethodField()

    class Meta:
        model = RasterFileLayer
        fields = ["id", "dataset", "name", "layerType", "multiTemporal", "isMultiLayer", "legendConfig", "nestedLegend",
                  "layerConfig", "params", "paramsSelectorConfig", "currentTimeMethod", "autoUpdateInterval", "canClip",
                  "analysisConfig", "tileJsonUrl"]

    def get_isMultiLayer(self, obj):
        return obj.dataset.multi_layer

    def get_nestedLegend(self, obj):
        return obj.dataset.multi_layer

    def get_autoUpdateInterval(self, obj):
        return obj.dataset.auto_update_interval_milliseconds

    def get_multiTemporal(self, obj):
        return obj.dataset.multi_temporal

    def get_layerType(self, obj):
        return obj.dataset.layer_type

    def get_name(self, obj):
        return obj.title

    def get_layerConfig(self, obj):
        request = self.context.get('request')
        layer_config = obj.layer_config(request)
        return layer_config

    def get_tileJsonUrl(self, obj):
        request = self.context.get('request')
        tile_json_url = obj.get_tile_json_url(request)
        return tile_json_url

    def get_params(self, obj):
        return obj.params

    def get_paramsSelectorConfig(self, obj):
        return obj.param_selector_config

    def get_legendConfig(self, obj):
        return obj.get_legend_config()

    def get_currentTimeMethod(self, obj):
        return obj.dataset.current_time_method

    def get_canClip(self, obj):
        return obj.dataset.can_clip

    def get_analysisConfig(self, obj):
        return obj.get_analysis_config()


class LayerRasterFileSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = LayerRasterFile
        fields = ["time", "id"]

    def get_time(self, obj):
        return obj.time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
