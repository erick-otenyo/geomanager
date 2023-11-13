import uuid

from django.contrib.admin.utils import quote
from django.contrib.gis.db import models
from django.core.files.base import ContentFile
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock

from geomanager.blocks import (
    InlineLegendBlock,
    FillVectorLayerBlock,
    LineVectorLayerBlock,
    CircleVectorLayerBlock,
    IconVectorLayerBlock,
    TextVectorLayerBlock,
    InlineIconLegendBlock
)
from geomanager.fields import ListField
from geomanager.helpers import get_vector_layer_files_url
from geomanager.models.core import Dataset, BaseLayer
from geomanager.models.vector_tile import VectorTileLayer
from geomanager.panels import ReadOnlyFieldPanel
from geomanager.utils.svg import rasterize_svg_to_png
from geomanager.utils.tiles import get_vector_render_layers
from geomanager.utils.vector_utils import drop_vector_table


class VectorFileLayer(TimeStampedModel, ClusterableModel, BaseLayer):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="vector_file_layers",
                                verbose_name=_("dataset"))
    render_layers = StreamField([
        ("fill", FillVectorLayerBlock(label=_("Polygon Layer"))),
        ("line", LineVectorLayerBlock(label=_("Line Layer"))),
        ("circle", CircleVectorLayerBlock(label=_("Point Layer"))),
        ("icon", IconVectorLayerBlock(label=_("Icon Layer"))),
        ("text", TextVectorLayerBlock(label=_("Text Label Layer"))),
    ], use_json_field=True, null=True, blank=True, min_num=1, verbose_name=_("Render Layers"))

    legend = StreamField([
        ('legend', InlineLegendBlock(label=_("Legend")),),
        ('legend_image', ImageChooserBlock(label=_("Legend Image")),),
        ('legend_icon', InlineIconLegendBlock(label=_("Legend Icon")),)
    ], use_json_field=True, null=True, blank=True, max_num=1, verbose_name=_("Legend"), )

    class Meta:
        verbose_name = _("Vector File Layer")
        verbose_name_plural = _("Vector File Layers")

    def __str__(self):
        return self.title

    def get_uploads_list_url(self):
        url = get_vector_layer_files_url(self.pk)
        return url

    @property
    def has_data_table(self):
        return self.vector_tables.all().exists()

    @property
    def upload_url(self):
        upload_url = reverse(
            f"geomanager_dataset_layer_upload_vector",
            args=[quote(self.dataset.pk), quote(self.pk)],
        )
        return upload_url

    @property
    def preview_url(self):
        preview_url = reverse(
            f"geomanager_preview_vector_layer",
            args=[quote(self.dataset.pk), quote(self.pk)],
        )
        return preview_url

    def layer_config(self, request=None):
        base_tiles_url = reverse("vector_tiles", args=(0, 0, 0))
        base_tiles_url = base_tiles_url.replace("/0/0/0", r"/{z}/{x}/{y}")

        if request:
            base_tiles_url = get_full_url(request, base_tiles_url)

        tile_url = f"{base_tiles_url}?table_name={{table_name}}"

        if self.dataset.can_clip:
            tile_url = tile_url + "&geostore_id={geostore_id}"

        layer_config = {
            "type": "vector",
            "source": {
                "type": "vector",
                "tiles": [tile_url]
            }
        }

        render_layers = get_vector_render_layers(self.render_layers)

        layer_config.update({"render": {"layers": render_layers}})

        return layer_config

    @property
    def params(self):
        recent = self.vector_tables.first()

        params = {
            "table_name": recent.table_name if recent else ""
        }

        if self.dataset.can_clip:
            params.update({"geostore_id": ""})

        return params

    @property
    def param_selector_config(self):
        config = {
            "key": "table_name",
            "required": True,
            "sentence": "{selector}",
        }

        return [config]

    def get_legend_config(self, request=None):
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

            if legend_block.block_type == "legend_image":
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

            config.update({"type": data.get("type", config.get("type"))})

            for item in data.get("items", []):
                config["items"].append({
                    "name": item.get("value"),
                    "color": item.get("color")
                })

        return config

    @property
    def interaction_config(self):
        config = {}

        # TODO: What happens if we have multiple tables ?
        vector_table = self.vector_tables.first()

        if vector_table and vector_table.properties:
            for column in vector_table.properties:
                if column.get("popup"):
                    if not config.get("output"):
                        config["output"] = []
                    name = column.get("name")
                    label = column.get("label")
                    config["output"].append({"column": name, "property": label or name}, )

        return config

    def save(self, *args, **kwargs):
        # remove existing icons for this layer.
        # TODO: Find efficient way to update exising icons, while deleting absolute ones
        VectorLayerIcon.objects.filter(layer=self).delete()

        for render_layer in self.render_layers:
            if render_layer.block_type == "icon":
                icon_image = render_layer.value.get("layout").get("icon_image")
                icon_color = render_layer.value.get("paint").get("icon_color")
                png_bytes = rasterize_svg_to_png(icon_image, fill_color=icon_color)

                if png_bytes:
                    layer_icon = VectorLayerIcon(name=icon_image, color=icon_color)
                    layer_icon.file = ContentFile(png_bytes.getvalue(), f"{icon_image}.{icon_color}.png")
                    self.icons.add(layer_icon)

        super().save(*args, **kwargs)


class VectorLayerIcon(models.Model):
    layer = ParentalKey(VectorFileLayer, on_delete=models.CASCADE, related_name="icons")
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=100, null=True)
    file = models.FileField(upload_to="vector_icons/")

    class Meta:
        verbose_name = _("Vector Layer Icon")
        verbose_name_plural = _("Vector Layer Icons")

    def __str__(self):
        return f"{self.layer.title}-{self.name}-{self.color}"


class VectorUpload(TimeStampedModel):
    dataset = models.ForeignKey(Dataset, blank=True, null=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to="vector_uploads")
    vector_metadata = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _("Vector Upload")
        verbose_name_plural = _("Vector Uploads")

    panels = [
        FieldPanel("dataset"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return f"{self.dataset} - {self.created}"


class PgVectorTable(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    layer = models.ForeignKey(VectorFileLayer, on_delete=models.CASCADE, related_name="vector_tables")
    table_name = models.CharField(max_length=256, unique=True)
    full_table_name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    time = models.DateTimeField(help_text=_("time for the dataset"))

    properties = models.JSONField()
    geometry_type = models.CharField(max_length=100)
    bounds = ListField(max_length=256)

    panels = [
        ReadOnlyFieldPanel("layer"),
        ReadOnlyFieldPanel("table_name"),
        ReadOnlyFieldPanel("full_table_name"),
        ReadOnlyFieldPanel("description"),
        ReadOnlyFieldPanel("time"),
        ReadOnlyFieldPanel("properties"),
        ReadOnlyFieldPanel("geometry_type"),
        ReadOnlyFieldPanel("bounds"),
    ]

    class Meta:
        ordering = ["-time"]
        unique_together = ('layer', 'time')
        verbose_name = _("Vector Upload")
        verbose_name_plural = _("Vector Uploads")

    def __str__(self):
        return f"{self.layer}  - {self.geometry_type}"

    @property
    def columns(self):
        if not self.properties:
            return []
        if self.properties:
            return [c.get("name") for c in self.properties]


@receiver(pre_delete, sender=PgVectorTable)
def drop_pg_vector_table(sender, instance, **kwargs):
    if instance.full_table_name:
        drop_vector_table(instance.full_table_name)


def get_legend_icons():
    vector_file_layers = VectorFileLayer.objects.all()
    vector_tile_layers = VectorTileLayer.objects.all()
    icons = []

    for layer in [*vector_file_layers, *vector_tile_layers]:
        if layer.legend:
            legend_block = layer.legend[0]
            if legend_block.block_type == "legend_icon":
                items = legend_block.value.get("items")
                for item in items:
                    icons.append(item.get("icon_image"))
    return icons
