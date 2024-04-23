import os

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.models import Image
from wagtail_modeladmin.helpers import AdminURLHelper

from geomanager.blocks import (
    FileLayerPointAnalysisBlock,
    FileLayerAreaAnalysisBlock, InlineLegendBlock
)
from geomanager.helpers import get_raster_layer_files_url
from geomanager.models.raster_style import RasterStyle
from geomanager.models.core import Dataset, BaseLayer
from geomanager.settings import geomanager_settings
from geomanager.storage import OverwriteStorage
from geomanager.utils import DATE_FORMAT_CHOICES
from geomanager.validators import validate_directory_name


class RasterFileLayer(TimeStampedModel, BaseLayer):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="raster_file_layers",
                                verbose_name=_("dataset"))
    date_format = models.CharField(max_length=100, choices=DATE_FORMAT_CHOICES, blank=True, null=True,
                                   default="yyyy-MM-dd HH:mm",
                                   verbose_name=_("Display Format for DateTime Selector"))
    style = models.ForeignKey("RasterStyle", null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("style"))
    use_custom_legend = models.BooleanField(default=False, verbose_name=_("Use custom legend"))
    legend = StreamField([
        ('legend', InlineLegendBlock(label=_("Custom Legend")),),
        ('legend_image', ImageChooserBlock(label=_("Custom Image")),),
    ], use_json_field=True, null=True, blank=True, max_num=1, verbose_name=_("Legend"), )

    auto_ingest_from_directory = models.BooleanField(default=False, verbose_name=_("Auto ingest from directory"))
    auto_ingest_use_custom_directory_name = models.BooleanField(default=False,
                                                                verbose_name=_("Use custom directory name"))
    auto_ingest_custom_directory_name = models.CharField(max_length=255, blank=True, null=True, unique=True,
                                                         validators=[validate_directory_name],
                                                         verbose_name=_("Custom directory name"))
    auto_ingest_nc_data_variable = models.CharField(max_length=100, blank=True, null=True,
                                                    verbose_name=_("Data variable for netCDF data auto ingest"),
                                                    help_text=_("The name of the data variable to use, "
                                                                "if ingesting from netCDF files"))

    analysis = StreamField([
        ('point_analysis', FileLayerPointAnalysisBlock(label=_("Point Analysis")),),
        ('area_analysis', FileLayerAreaAnalysisBlock(label=_("Area Analysis")),),
    ], block_counts={'point_analysis': {'max_num': 1}, 'area_analysis': {'max_num': 1}}, use_json_field=True,
        null=True, blank=True, max_num=2, verbose_name=_("Analysis"), )

    class Meta:
        verbose_name = _("Raster File Layer")
        verbose_name_plural = _("Raster File Layers")
        ordering = ['order']

    panels = [
        FieldPanel("dataset"),
        FieldPanel("title"),
        FieldPanel("default"),
        FieldPanel("date_format"),
        FieldPanel("style"),
        FieldPanel("use_custom_legend"),
        FieldPanel("legend"),
        FieldPanel("auto_ingest_from_directory"),

        MultiFieldPanel([
            FieldPanel("auto_ingest_use_custom_directory_name"),
            FieldPanel("auto_ingest_custom_directory_name", classname="show-if-custom-dir-name"),
            FieldPanel("auto_ingest_nc_data_variable"),
        ], heading=_("Auto ingest settings")),

        FieldPanel("analysis"),
    ]

    def __str__(self):
        return f"{self.dataset.title} - {self.title}"

    @property
    def raster_files_count(self):
        return self.raster_files.count()

    def get_uploads_list_url(self):
        url = get_raster_layer_files_url(self.pk)
        return url

    def get_style_url(self):
        url = {"action": _("Create Style")}
        style_admin_helper = AdminURLHelper(RasterStyle)
        if self.style:
            url.update({
                "action": _("Edit Style"),
                "url": style_admin_helper.get_action_url("edit", self.style.pk)
            })
        else:
            url.update({
                "url": style_admin_helper.get_action_url("create") + f"?layer_id={self.pk}"
            })
        return url

    @property
    def base_tile_url(self):
        base_tiles_url = reverse("raster_tiles", args=(self.id, 0, 0, 0))
        base_tiles_url = base_tiles_url.replace("/0/0/0", r"/{z}/{x}/{y}")
        return f"{base_tiles_url}"

    def get_tile_json_url(self, request=None):
        tile_json_url = reverse("raster_file_tile_json", args=(self.id,))
        if request:
            tile_json_url = get_full_url(request, tile_json_url)

        return tile_json_url

    def layer_config(self, request=None):
        base_tile_url = self.base_tile_url
        if request:
            base_tile_url = get_full_url(request, base_tile_url)

        tile_url = f"{base_tile_url}?time={{time}}"

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
        if self.dataset.multi_layer:
            default_layer = self.dataset.layers.filter(default=True).exclude(pk=self.pk).first()
            if default_layer:
                return default_layer.param_selector_config

        time_config = {
            "key": "time",
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
            elif self.date_format == "dekadal":
                time_config.update({
                    "dateFormat": {"currentTime": "MMM yyyy", "asPeriod": "dekadal"},
                })
            else:
                time_config.update({
                    "dateFormat": {"currentTime": self.date_format},
                })
        else:
            time_config.update({
                "dateFormat": {"currentTime": "yyyy-MM-dd HH:mm"},
            })

        return [time_config]

    def get_legend_config(self, request=None):
        config = {
            "type": "choropleth",
            "items": []
        }

        if self.style:
            if self.use_custom_legend:
                legend_block = self.legend

                # only one legend block entry is expected
                if legend_block:
                    legend_block = legend_block[0]

                if legend_block:
                    if isinstance(legend_block.value, Image):
                        image_url = legend_block.value.file.url
                        image_url = get_full_url(request, image_url)
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

            return self.style.get_legend_config()

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

    def get_tile_json(self, request=None):
        base_tile_url = self.base_tile_url
        timestamps = list(self.raster_files.all().values_list("time", flat=True))

        if request:
            base_tile_url = get_full_url(request, base_tile_url)

        tile_json = {
            "tilejson": "3.0.0",
            "name": self.title,
            "scheme": "xyz",
            "tiles": [base_tile_url],
            "minzoom": 0,
            "maxzoom": 20,
            "time_parameter": "time",
            "timestamps": [t.strftime("%Y-%m-%dT%H:%M:%S.000Z") for t in timestamps]
        }

        return tile_json

    def clean(self):
        # if adding a layer to a dataset that already has a layer and is not multi layer
        if self._state.adding:
            if self.dataset.has_layers() and not self.dataset.multi_layer:
                raise ValidationError(_("Can not add layer because the dataset is not marked as Multi Layer. "
                                        "To add multiple layers to a dataset, please mark the dataset as "
                                        "Multi Layer and try again"))


@receiver(post_save, sender=RasterFileLayer)
def create_auto_ingest_directory(sender, instance, created, **kwargs):
    if instance.auto_ingest_from_directory:
        auto_ingest_raster_data_dir = geomanager_settings.get("auto_ingest_raster_data_dir")

        dir_name = str(instance.pk)

        if auto_ingest_raster_data_dir and os.path.isabs(auto_ingest_raster_data_dir):

            if instance.auto_ingest_use_custom_directory_name and instance.auto_ingest_custom_directory_name:
                dir_name = instance.auto_ingest_custom_directory_name

            if not os.path.exists(auto_ingest_raster_data_dir):
                os.makedirs(auto_ingest_raster_data_dir)

            directory_path = os.path.join(auto_ingest_raster_data_dir, dir_name)

            # Create the directory if it doesn't exist
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)


def layer_raster_file_dir_path(instance, filename):
    file_dir = f"raster_files/{type(instance.layer).__name__}-{instance.layer.pk}/{filename}"
    return file_dir


class LayerRasterFile(TimeStampedModel):
    layer = models.ForeignKey(RasterFileLayer, on_delete=models.CASCADE, related_name="raster_files",
                              verbose_name=_("layer"))
    file = models.FileField(upload_to=layer_raster_file_dir_path, storage=OverwriteStorage, verbose_name=_("file"))
    time = models.DateTimeField(verbose_name=_("time"),
                                help_text=_("Time for the raster file. This can be the time the data was acquired, "
                                            "or the date and time for which the data applies", ))
    raster_metadata = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Layer Raster File")
        verbose_name_plural = _("Layer Raster Files")
        ordering = ["-time"]
        unique_together = ('layer', 'time')

    panels = [
        FieldPanel("time"),
        FieldPanel("raster_metadata", read_only=True),
    ]

    def __str__(self):
        return f"{self.layer.title} - {self.time}"

    @property
    def thumbnail_url(self):
        url = reverse("raster_file_thumbnail", kwargs={"file_id": self.pk})
        return url

    @property
    def time_str(self):
        return self.time.strftime("%Y-%m-%dT%H:%M:%S.000Z")


class RasterUpload(TimeStampedModel):
    dataset = models.ForeignKey(Dataset, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("dataset"))
    file = models.FileField(upload_to="raster_uploads", verbose_name=_("file"))
    raster_metadata = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Raster Upload")
        verbose_name_plural = _("Raster Uploads")

    panels = [
        FieldPanel("layer"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return f"{self.dataset} - {self.created}"
