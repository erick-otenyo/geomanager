from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, InlinePanel
from wagtail.contrib.modeladmin.helpers import AdminURLHelper
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import Image
from wagtail.models import Orderable
from wagtail_color_panel.edit_handlers import NativeColorPanel
from wagtail_color_panel.fields import ColorField

from geomanager.blocks import (
    WmsRequestParamSelectableBlock,
    InlineLegendBlock,
    FileLayerPointAnalysisBlock,
    FileLayerAreaAnalysisBlock
)
from geomanager.forms import RasterStyleModelForm
from geomanager.helpers import get_raster_layer_files_url
from geomanager.models.core import Dataset, BaseLayer
from geomanager.widgets import RasterStyleWidget


class FileImageLayer(TimeStampedModel, BaseLayer):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="file_layers",
                                verbose_name=_("dataset"))
    style = models.ForeignKey("RasterStyle", null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("style"))

    analysis = StreamField([
        ('point_analysis', FileLayerPointAnalysisBlock(label=_("Point Analysis")),),
        ('area_analysis', FileLayerAreaAnalysisBlock(label=_("Area Analysis")),),
    ], block_counts={'point_analysis': {'max_num': 1}, 'area_analysis': {'max_num': 1}}, use_json_field=True,
        null=True, blank=True, max_num=2, verbose_name=_("Analysis"), )

    panels = [
        FieldPanel("dataset"),
        FieldPanel("title"),
        FieldPanel("default"),
        FieldPanel("style"),
        FieldPanel("analysis")
    ]

    def __str__(self):
        return f"{self.dataset.title} - {self.title}"

    def get_uploads_list_url(self):
        url = get_raster_layer_files_url(self.pk)
        return url

    def get_style_url(self):
        url = {"action": "Create Style"}
        style_admin_helper = AdminURLHelper(RasterStyle)
        if self.style:
            url.update({
                "action": "Edit Style",
                "url": style_admin_helper.get_action_url("edit", self.style.pk)
            })
        else:
            url.update({
                "url": style_admin_helper.get_action_url("create") + f"?layer_id={self.pk}"
            })
        return url

    def layer_config(self, request=None):
        base_tiles_url = reverse("raster_tiles", args=(0, 0, 0))
        base_tiles_url = base_tiles_url.replace("/0/0/0", r"/{z}/{x}/{y}")

        if request:
            base_absolute_url = request.scheme + '://' + request.get_host()
            base_tiles_url = base_absolute_url + base_tiles_url

        tile_url = f"{base_tiles_url}?layer={self.id}&time={{time}}"

        if self.dataset.can_clip:
            tile_url = tile_url + "&geostore_id={geostore_id}"

        layer_config = {
            "type": "raster",
            "source": {
                "type": "raster",
                "tiles": [tile_url]
            }
        }

        return layer_config

    @property
    def params(self):
        params = {
            "time": ""
        }

        if self.dataset.can_clip:
            params.update({"geostore_id": ""})

        return params

    @property
    def param_selector_config(self):
        config = {
            "key": "time",
            "required": True,
            "sentence": "{selector}",
            "type": "datetime",
            "dateFormat": {"currentTime": "yyyy-mm-dd HH:MM"},
            "availableDates": [],
        }
        return [config]

    def get_legend_config(self):
        if self.style:
            return self.style.get_legend_config()

        config = {}
        return config

    def get_analysis_config(self):
        analysis_config = {}

        for analysis in self.analysis:
            data = analysis.block.get_api_representation(analysis.value)

            if analysis.block_type == "point_analysis":
                unit = data.get("unit")
                if data.get("instance_data_enabled"):
                    analysis_config.update({
                        "pointInstanceAnalysis": {"unit": unit}
                    })
                if data.get("timeseries_data_enabled"):
                    analysis_config.update({
                        "pointTimeseriesAnalysis": {
                            "unit": unit,
                            "chartType": data.get("timeseries_chart_type"),
                            "chartColor": data.get("timeseries_chart_color")
                        }
                    })
            if analysis.block_type == "area_analysis":
                unit = data.get("unit")
                if data.get("instance_data_enabled"):
                    analysis_config.update({
                        "areaInstanceAnalysis": {
                            "unit": unit,
                            "valueType": data.get("instance_value_type")
                        }
                    })
                if data.get("timeseries_data_enabled"):
                    analysis_config.update({
                        "areaTimeseriesAnalysis": {
                            "unit": unit,
                            "aggregationMethod": data.get("timeseries_aggregation_method"),
                            "chartType": data.get("timeseries_chart_type"),
                            "chartColor": data.get("timeseries_chart_color")
                        }
                    })

        return analysis_config

    def clean(self):
        # if adding a layer to a dataset that already has a layer and is not multi layer
        if self._state.adding:
            if self.dataset.has_layers() and not self.dataset.multi_layer:
                raise ValidationError(
                    "Can not add layer because the dataset is not marked as Multi Layer. "
                    "To add multiple layers to a dataset, please mark the dataset as Multi Layer and try again")


def layer_raster_file_dir_path(instance, filename):
    file_dir = f"raster_files/{type(instance.layer).__name__}-{instance.layer.pk}/{filename}"
    return file_dir


class LayerRasterFile(TimeStampedModel):
    layer = models.ForeignKey(FileImageLayer, on_delete=models.CASCADE, related_name="raster_files",
                              verbose_name=_("layer"))
    file = models.FileField(upload_to=layer_raster_file_dir_path, verbose_name=_("file"))
    time = models.DateTimeField(verbose_name=_("time"),
                                help_text="Time for the raster file. This can be the time the data was acquired, "
                                          "or the date and time for which the data applies", )

    class Meta:
        ordering = ["time"]
        unique_together = ('layer', 'time')

    panels = [
        FieldPanel("time"),
    ]

    def __str__(self):
        return f"{self.time}"


class RasterUpload(TimeStampedModel):
    dataset = models.ForeignKey(Dataset, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("dataset"))
    file = models.FileField(upload_to="raster_uploads", verbose_name=_("file"))
    raster_metadata = models.JSONField(blank=True, null=True)

    panels = [
        FieldPanel("layer"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return f"{self.dataset} - {self.created}"


class RasterStyle(TimeStampedModel, ClusterableModel):
    base_form_class = RasterStyleModelForm

    name = models.CharField(max_length=256, verbose_name=_("name"),
                            help_text=_("Style name for identification"))
    unit = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("data unit"),
                            help_text=_("Data unit"))
    min = models.IntegerField(default=0, verbose_name=_("minimum value"), help_text=_("minimum value"))
    max = models.IntegerField(default=100, verbose_name=_("maximum value"), help_text=_("maximum value"))
    steps = models.IntegerField(default=5, validators=[MinValueValidator(3), MaxValueValidator(20), ], null=True,
                                blank=True, verbose_name=_("steps"), help_text=_("Number of steps"))
    use_custom_colors = models.BooleanField(default=False, verbose_name=_("Use Custom Colors"))
    palette = models.TextField(blank=True, null=True, verbose_name=_("Color Palette"))
    interpolate = models.BooleanField(default=False, verbose_name=_("interpolate"), help_text="Interpolate colorscale")
    custom_color_for_rest = ColorField(blank=True, null=True, default="#ff0000",
                                       verbose_name=_("Color for the rest of values"),
                                       help_text=_(
                                           "Color for values greater than the values defined above, "
                                           "as well as values greater than the maximum defined value"))

    def __str__(self):
        return self.name

    panels = [
        FieldPanel("name"),
        FieldPanel("unit"),
        FieldRowPanel(
            [
                FieldPanel("min"),
                FieldPanel("max"),
            ], _("Data values")
        ),
        FieldPanel("steps"),
        FieldPanel("palette", widget=RasterStyleWidget),
        FieldPanel("use_custom_colors"),
        MultiFieldPanel([
            InlinePanel("color_values", heading=_("Color Values"), label=_("Color Value")),
            NativeColorPanel("custom_color_for_rest"),
        ], _("Custom Color Values")),

        # FieldPanel("interpolate")
    ]

    def get_palette_list(self):
        if not self.use_custom_colors:
            return self.palette.split(",")
        return self.get_custom_palette()

    @property
    def min_value(self):
        return self.min

    @property
    def max_value(self):
        max_value = self.max
        if self.min == max_value:
            max_value += 0.1
        return max_value

    @property
    def scale_value(self):
        return 254 / (self.max_value - self.min_value)

    @property
    def offset_value(self):
        return -self.min_value

    @property
    def clip_value(self):
        return self.max_value + self.offset_value

    def get_custom_color_values(self):
        values = []
        color_values = self.color_values.order_by('threshold')

        for i, c_value in enumerate(color_values):
            value = c_value.value
            # if not the first one, add prev value for later comparison
            if i == 0:
                value["min_value"] = None
            else:
                value["min_value"] = color_values[i - 1].threshold
            value["max_value"] = value["threshold"]
            values.append(value)
        return values

    def get_custom_palette(self):
        colors = []
        for i in range(256):
            color = self.get_color_for_index(i)
            colors.append(color)

        return colors

    def get_color_for_index(self, index_value):
        values = self.get_custom_color_values()

        for value in values:
            max_value = value["max_value"] + self.offset_value

            if max_value > self.clip_value:
                max_value = self.clip_value

            if max_value < 0:
                max_value = 0

            max_value = self.scale_value * max_value

            if value["min_value"] is None:
                if index_value <= max_value:
                    return values[0]["color"]

            if value["min_value"] is not None:
                min_value = value["min_value"] + self.offset_value

                if min_value > self.clip_value:
                    min_value = self.clip_value

                if min_value < 0:
                    min_value = 0

                min_value = self.scale_value * min_value

                if min_value < index_value <= max_value:
                    return value["color"]

        return self.custom_color_for_rest

    def get_style_as_json(self):
        palette = self.get_palette_list()
        style = {
            "bands": [
                {
                    "band": 1,
                    "min": self.min,
                    "max": self.max,
                    "palette": palette,
                    "scheme": "discrete",
                }
            ]
        }
        return style

    def get_legend_config(self):
        items = []
        if self.use_custom_colors:
            values = self.get_custom_color_values()
            count = len(values)
            if count > 1:
                for value in values:
                    item = {
                        "name": value['label'] if value.get('label') else value['threshold'],
                        "color": value['color']
                    }
                    items.append(item)
                rest_item = {"name": "", "color": self.custom_color_for_rest}
                items.append(rest_item)

        return {"type": "choropleth", "items": items}


class ColorValue(TimeStampedModel, Orderable):
    layer = ParentalKey(RasterStyle, related_name='color_values')
    threshold = models.FloatField(verbose_name=_("Threshold value"), help_text=_(
        "Values less than or equal to the input value, will be assigned the chosen color"))
    color = ColorField(default="#ff0000", verbose_name=_("color"))
    label = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Label for Legend'))

    class Meta:
        verbose_name = _("Color Value")
        verbose_name_plural = _("Color Values")

    panels = [
        FieldPanel("threshold"),
        NativeColorPanel("color"),
        FieldPanel("label")
    ]

    @property
    def value(self):
        return {
            "threshold": self.threshold,
            "color": self.color,
            "label": self.label
        }


class WmsLayer(TimeStampedModel, ClusterableModel, BaseLayer):
    OUTPUT_FORMATS = (
        ("image/png", "PNG"),
        ("image/jpeg", "JPEG"),
        ("image/gif", "GIF"),
    )

    VERSION_CHOICES = (
        ("1.1.1", "1.1.1"),
        ("1.3.0", "1.3.0"),
    )

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="wms_layers", verbose_name=_("dataset"))

    base_url = models.CharField(max_length=500, verbose_name=_("base url for WMS"),
                                )
    version = models.CharField(max_length=50, default="1.1.1", choices=VERSION_CHOICES, verbose_name=_("WMS Version"))
    width = models.IntegerField(default=256, verbose_name=_("Pixel Width"),
                                help_text=_("The size of the map image in pixels along the i axis"), )
    height = models.IntegerField(default=256, verbose_name=_("Pixel Height"),
                                 help_text=_("The size of the map image in pixels along the j axis"), )
    transparent = models.BooleanField(default=True, verbose_name=_("Transparency"),
                                      help_text=_("Ability of underlying maps to be visible or not"), )
    srs = models.CharField(max_length=50, default="EPSG:3857", verbose_name=_("Spatial Reference System"),
                           help_text=_("WMS Spatial Reference e.g EPSG:3857"), )
    format = models.CharField(max_length=50, default="image/png", choices=OUTPUT_FORMATS,
                              verbose_name=_("Output Format"),
                              help_text=_(
                                  "Allowed map formats are either “picture” formats or “graphic element” formats."), )
    wms_query_params_selectable = StreamField([
        ('param', WmsRequestParamSelectableBlock(label=_("Query Parameter")))
    ], use_json_field=True, null=True, blank=True, verbose_name=_("WMS Query Params With selectable Options"),
        help_text=_(
            "This should provide a list of options that users can choose to change the query parameter of the url"))

    params_selectors_side_by_side = models.BooleanField(default=False,
                                                        verbose_name=_("Arrange Param Selectors side by side"))
    legend = StreamField([
        ('legend', InlineLegendBlock(label=_("Custom Legend")),),
        ('legend_image', ImageChooserBlock(label=_("Custom Image")),),
    ], use_json_field=True, null=True, blank=True, max_num=1, verbose_name=_("Legend"), )

    panels = [
        FieldPanel("dataset"),
        FieldPanel("title"),
        FieldPanel("default"),
        MultiFieldPanel([
            FieldPanel("base_url"),
            FieldPanel("version"),
            FieldRowPanel([
                FieldPanel("width", classname="col6"),
                FieldPanel("height", classname="col6"),
            ]),
            FieldPanel("transparent"),
            FieldPanel("srs"),
            FieldPanel("format"),
            InlinePanel("wms_request_layers", heading=_("WMS Request Layers"),
                        label=_("WMS Request Layer"), min_num=1),
            InlinePanel("wms_request_styles", heading=_("WMS Request Styles"),
                        label=_("WMS Request Style")),
            InlinePanel("wms_request_params", heading=_("WMS Request Additional Parameters"),
                        label=_("WMS Request Param")),
            FieldPanel("wms_query_params_selectable"),

        ], heading="WMS Configuration"),
        FieldPanel("params_selectors_side_by_side"),
        FieldPanel("legend"),
    ]

    def __str__(self):
        return self.title

    def get_selectable_params(self):
        params = {}
        if self.wms_query_params_selectable:
            for query_param in self.wms_query_params_selectable:
                data = query_param.block.get_api_representation(query_param.value)
                val = f"{data.get('name')}"
                params.update({val: data})
        return params

    def get_wms_params(self):
        params = {
            "SERVICE": "WMS",
            "CRS": self.srs,
            "VERSION": self.version,
            "REQUEST": "GetMap",
            "TRANSPARENT": self.transparent,
            "LAYERS": ",".join([layer.name for layer in self.wms_request_layers.all()]),
            "STYLES": ",".join([style.name for style in self.wms_request_styles.all()]),
            "BBOX": "{bbox-epsg-3857}",
            "WIDTH": self.width,
            "HEIGHT": self.height,
            "FORMAT": self.format,
        }

        extra_params = {param.name: param.value for param in self.wms_request_params.all()}
        params.update(**extra_params)

        return params

    @property
    def get_map_url(self):
        params = self.get_wms_params()
        selectable_params = self.get_selectable_params()

        for key, val in selectable_params.items():
            key_val = key
            if key.upper() in params:
                key_val = key.upper()
            params.update({key_val: f"{{{key}}}"})

        query_str = '&'.join([f"{key}={value}" for key, value in params.items()])
        request_url = f"{self.base_url}?{query_str}"

        return request_url

    def get_selectable_params_config(self):
        selectable_params = self.get_selectable_params()
        config = []

        for key, param_config in selectable_params.items():
            param_config = {
                "key": key,
                "required": True,
                "type": param_config.get("type"),
                "options": param_config.get("options"),
                "sentence": f"{param_config.get('label') or key} {{selector}}",
            }

            config.append(param_config)

        return config

    @property
    def get_capabilities_url(self):
        params = {
            "SERVICE": "WMS",
            "VERSION": self.version,
            "REQUEST": "GetCapabilities",
        }
        query_str = '&'.join([f"{key}={value}" for key, value in params.items()])
        request_url = f"{self.base_url}?{query_str}"
        return request_url

    @property
    def layer_config(self):
        wms_url = self.get_map_url
        if self.dataset.multi_temporal:
            wms_url = f"{wms_url}&time={{time}}"

        layer_config = {
            "type": "raster",
            "source": {
                "type": "raster",
                "tiles": [wms_url]
            }
        }

        return layer_config

    @property
    def params(self):
        params = {}
        if self.dataset.multi_temporal:
            params.update({"time": ""})

        selector_config = self.get_selectable_params_config()

        for selector_param in selector_config:
            default = None
            for option in selector_param.get("options"):
                if option.get("default"):
                    default = option.get("value")
                    break
            if not default:
                default = selector_param.get("options")[0].get("value")
            params.update({selector_param.get("key"): default})

        return params

    @property
    def param_selector_config(self):
        config = []

        if self.dataset.multi_temporal:
            time_config = {
                "key": "time",
                "required": True,
                "sentence": "{selector}",
                "type": "datetime",
                "dateFormat": {"currentTime": "yyyy-mm-dd HH:MM"},
                "availableDates": [],
            }

            config.append(time_config)
        selectable_params_config = self.get_selectable_params_config()

        config.extend(selectable_params_config)

        return config

    def get_legend_config(self, request):

        # default config
        config = {
            "type": "basic",
            "items": []
        }

        legend_block = self.legend

        # only one legend block entry is expected
        if legend_block:
            legend_block = legend_block[0]

        if legend_block:
            if isinstance(legend_block.value, Image):
                image_url = legend_block.value.file.url
                if request:
                    image_url = request.build_absolute_uri(image_url)
                config.update({"type": "image", "imageUrl": image_url})
                return config

            data = legend_block.block.get_api_representation(legend_block.value)

            config.update({"type": data.get("type")})

            for item in data.get("items"):
                config["items"].append({
                    "name": item.get("value"),
                    "color": item.get("color")
                })

        return config

    @property
    def layer_name(self):
        return self.wms_request_layers.all()[0].name

    def get_analysis_config(self):
        analysis_config = []

        return analysis_config


class WmsRequestLayer(Orderable):
    layer = ParentalKey(WmsLayer, on_delete=models.CASCADE, related_name="wms_request_layers",
                        verbose_name=_("WMS Request Layers"))
    name = models.CharField(max_length=250, null=False, blank=False,
                            verbose_name=_("name"),
                            help_text=_("WMS Layer is requested by using this "
                                        "name in the LAYERS parameter of a "
                                        "GetMap request."))


class WmsRequestStyle(Orderable):
    layer = ParentalKey(WmsLayer, on_delete=models.CASCADE,
                        related_name="wms_request_styles", verbose_name=_("WMS Request Styles"))
    name = models.CharField(max_length=250, null=False, blank=False,
                            verbose_name=_("name"),
                            help_text=_("The style's Name is used in the Map request STYLES parameter"))


class WmsRequestParam(Orderable):
    layer = ParentalKey(WmsLayer, on_delete=models.CASCADE, related_name="wms_request_params",
                        verbose_name=_("WMS Requests Additional Parameters", ))
    name = models.CharField(max_length=250, null=False, blank=False, verbose_name=_("name"),
                            help_text=_("Name of the parameter"))
    value = models.CharField(max_length=250, null=False, blank=False, help_text=_("Value of the parameter"))
