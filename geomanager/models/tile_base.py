from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import Image

from geomanager.blocks import (
    InlineLegendBlock,
    LayerMoreInfoBlock,
    QueryParamSelectableBlock,
    QueryParamStaticBlock, InlineIconLegendBlock
)
from geomanager.models.core import BaseLayer
from geomanager.utils import DATE_FORMAT_CHOICES


class BaseTileLayer(TimeStampedModel, ClusterableModel, BaseLayer):
    class Meta:
        abstract = True

    base_url = models.CharField(max_length=500, verbose_name=_("Base Tile url"), )

    query_params_static = StreamField([
        ('param', QueryParamStaticBlock(label=_("Query Parameter")))
    ], use_json_field=True, null=True, blank=True, verbose_name=_("Static Query Params"),
        help_text=_("Static query params to be added to the url"))

    query_params_selectable = StreamField([
        ('param', QueryParamSelectableBlock(label=_("Selectable Query Parameter")))
    ], use_json_field=True, null=True, blank=True, verbose_name=_("Query Params With selectable Options"),
        help_text=_("This should provide a list of options that users "
                    "can choose to change the query parameter of the url"))

    params_selectors_side_by_side = models.BooleanField(default=False,
                                                        verbose_name=_("Arrange Param Selectors side by side"))

    legend = StreamField([
        ('legend', InlineLegendBlock(label=_("Custom Legend")),),
        ('legend_image', ImageChooserBlock(label=_("Custom Image")),),
        ('legend_icon', InlineIconLegendBlock(label=_("Legend Icon")),),
    ], use_json_field=True, null=True, blank=True, max_num=1, verbose_name=_("Legend"), )

    more_info = StreamField([
        ('more_info', LayerMoreInfoBlock(label=_("Info link")),),
    ], block_counts={
        'more_info': {'max_num': 1},
    }, use_json_field=True, null=True, blank=True, max_num=1, verbose_name=_("More Info"), )

    get_time_from_tile_json = models.BooleanField(default=False, verbose_name=_("Get time from tile json url"))
    tile_json_url = models.URLField(max_length=500, blank=True, null=True, verbose_name=_("Tile JSON url"))
    timestamps_response_object_key = models.CharField(max_length=100, blank=True, null=True, default="timestamps",
                                                      verbose_name=_("Timestamps response object key"),
                                                      help_text=_("Key for timestamps values in response object"))
    date_format = models.CharField(max_length=100, choices=DATE_FORMAT_CHOICES, blank=True, null=True,
                                   verbose_name=_("Display Format for DateTime Selector"))
    time_parameter_name = models.CharField(max_length=100, blank=True, null=True, default="time",
                                           verbose_name=_("Time Parameter Name"),
                                           help_text=_("Name of the time parameter in the url"))

    panels = [
        FieldPanel("title"),
        FieldPanel("default"),
        FieldPanel("base_url"),

        MultiFieldPanel([
            FieldPanel("get_time_from_tile_json"),
            FieldPanel("tile_json_url", classname="show_if_get_time_checked"),
            FieldPanel("timestamps_response_object_key", classname="show_if_get_time_checked"),
            FieldPanel("time_parameter_name", classname="show_if_get_time_checked"),
            FieldPanel("date_format", classname="show_if_get_time_checked"),
        ], heading=_("Time Settings")),

        FieldPanel("query_params_static"),
        FieldPanel("query_params_selectable"),
        FieldPanel("params_selectors_side_by_side"),
        FieldPanel("legend"),
        FieldPanel("more_info"),
    ]

    @property
    def tile_url(self):
        tile_url = self.base_url

        query_params = {}

        if self.has_time:
            time_param_name = self.time_parameter_name or "time"
            query_params.update({
                time_param_name: "{{time}}"
            })

        static_params = self.get_static_params()
        if static_params:
            query_params.update(static_params)

        query_str = '&'.join([f"{key}={value}" for key, value in query_params.items()])

        if query_str:
            tile_url = f"{tile_url}?{query_str}"

        return tile_url

    def get_selectable_params(self):
        params = {}
        if self.query_params_selectable:
            for query_param in self.query_params_selectable:
                data = query_param.block.get_api_representation(query_param.value)
                val = f"{data.get('name')}"
                params.update({val: data})
        return params

    def get_static_params(self):
        params = {}
        if self.query_params_static:
            for query_param in self.query_params_static:
                data = query_param.block.get_api_representation(query_param.value)
                val = f"{data.get('key')}"
                params.update({val: data.get('value')})
        return params

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
    def has_time(self):
        return bool(self.dataset.multi_temporal and self.get_time_from_tile_json and self.tile_json_url)

    @property
    def params(self):
        params = {}
        if self.has_time:
            time_param_name = self.time_parameter_name or "time"
            params.update({time_param_name: ""})

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
        time_param_name = self.time_parameter_name or "time"
        if self.has_time:
            time_config = {
                "key": "time",
                "url_param": time_param_name,
                "required": True,
                "sentence": "{selector}",
                "type": "datetime",
                "availableDates": [],
            }

            if self.date_format:
                if self.date_format == "pentadal":
                    time_config.update({
                        "dateFormat": {"currentTime": "MMM yyyy", "asPeriod": "pentadal"},
                    })
                else:
                    time_config.update({
                        "dateFormat": {"currentTime": self.date_format},
                    })
            else:
                time_config.update({
                    "dateFormat": {"currentTime": "yyyy-MM-dd HH:mm"},
                })

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
                    image_url = get_full_url(request, image_url)
                config.update({"type": "image", "imageUrl": image_url})
                return config

            data = legend_block.block.get_api_representation(legend_block.value)

            if legend_block.block_type == "legend_icon":
                for item in data.get("items", []):
                    config["items"].append({
                        "icon": item.get("icon_image"),
                        "name": item.get("icon_label"),
                        "color": item.get("icon_color"),
                        "iconSource": "sprite",
                    })
                return config

            config.update({"type": data.get("type")})

            for item in data.get("items"):
                config["items"].append({
                    "name": item.get("value"),
                    "color": item.get("color")
                })

        return config
