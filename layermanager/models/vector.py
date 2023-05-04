import uuid

from django.contrib.admin.utils import quote
from django.contrib.gis.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet

from layermanager.blocks import InlineLegendBlock
from layermanager.fields import ListField
from layermanager.models import Dataset
from layermanager.models.core import BaseLayer
from layermanager.utils.vector_utils import drop_vector_table


class CountryBoundary(TimeStampedModel):
    name_0 = models.CharField(max_length=100, blank=True, null=True)
    name_1 = models.CharField(max_length=100, blank=True, null=True)
    name_2 = models.CharField(max_length=100, blank=True, null=True)
    gid_0 = models.CharField(max_length=100, blank=True, null=True)
    gid_1 = models.CharField(max_length=100, blank=True, null=True)
    gid_2 = models.CharField(max_length=100, blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)

    geom = models.MultiPolygonField(srid=4326)

    class Meta:
        verbose_name_plural = _("Country Boundaries")

    def __str__(self):
        return str(self.pk)

    @property
    def bbox(self):
        min_x, min_y, max_x, max_y = self.geom.envelope.extent
        bbox = [min_x, min_y, max_x, max_y]
        return bbox

    @property
    def info(self):
        info = {"iso": self.gid_0}

        if self.level == 0:
            info.update({"name": self.name_0})

        if self.level == 1:
            gid_1 = self.gid_1.split(".")[1].split("_")[0]
            info.update({"id1": gid_1, "name": self.name_1})

        if self.level == 2:
            gid_1 = self.gid_1.split(".")[1].split("_")[0]
            gid_2 = self.gid_1.split(".")[1].split("_")[1]
            info.update({"id1": gid_1, "id2": gid_2, "name": self.name_2})

        return info


class Geostore(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    iso = models.CharField(max_length=100, blank=True, null=True)
    id1 = models.CharField(max_length=100, blank=True, null=True)
    id2 = models.CharField(max_length=100, blank=True, null=True)

    name_0 = models.CharField(max_length=100, blank=True, null=True)
    name_1 = models.CharField(max_length=100, blank=True, null=True)
    name_2 = models.CharField(max_length=100, blank=True, null=True)

    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.id.hex

    @property
    def bbox(self):
        min_x, min_y, max_x, max_y = self.geom.envelope.extent
        bbox = [min_x, min_y, max_x, max_y]
        return bbox

    @property
    def info(self):

        info = {}

        if self.iso:
            info.update({"iso": self.iso, "name": self.name_0})

        if self.id1:
            info.update({"id1": self.id1, "name": self.name_1})

        if self.id2:
            info.update({"id2": self.id2, "name": self.name_2})

        return info


class VectorLayer(TimeStampedModel, BaseLayer):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="vector_layers", verbose_name="dataset")
    legend = StreamField([
        ('legend', InlineLegendBlock(label=_("Legend")),),
        ('legend_image', ImageChooserBlock(),)
    ], use_json_field=True, null=True, blank=True, max_num=1, verbose_name=_("Legend"), )

    @property
    def upload_url(self):
        upload_url = reverse(
            f"layermanager_dataset_layer_upload_vector",
            args=[quote(self.dataset.pk), quote(self.pk)],
        )
        return upload_url

    @property
    def preview_url(self):
        preview_url = reverse(
            f"layermanager_preview_vector_layer",
            args=[quote(self.dataset.pk), quote(self.pk)],
        )
        return preview_url

    def __str__(self):
        return self.title

    def layer_config(self, request=None):
        base_tiles_url = "/api/vector-tiles/{z}/{x}/{y}"

        if request:
            base_absolute_url = request.scheme + '://' + request.get_host()
            base_tiles_url = base_absolute_url + base_tiles_url

        tile_url = f"{base_tiles_url}?table_name={{table_name}}"

        layer_config = {
            "type": "vector",
            "source": {
                "type": "vector",
                "tiles": [tile_url]
            }
        }

        return layer_config


class VectorUpload(TimeStampedModel):
    dataset = models.ForeignKey(Dataset, blank=True, null=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to="vector_uploads")
    vector_metadata = models.JSONField(blank=True, null=True)

    panels = [
        FieldPanel("dataset"),
        FieldPanel("file"),
    ]

    def __str__(self):
        return f"{self.dataset} - {self.created}"


@register_snippet
class PgVectorTable(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    layer = models.ForeignKey(VectorLayer, on_delete=models.CASCADE, related_name="vector_tables")
    table_name = models.CharField(max_length=256, unique=True)
    full_table_name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    time = models.DateTimeField(help_text="time for the dataset")

    properties = models.JSONField()
    geometry_type = models.CharField(max_length=100)
    bounds = ListField(max_length=256)

    class Meta:
        ordering = ["-time"]
        unique_together = ('layer', 'time')


@receiver(pre_delete, sender=PgVectorTable)
def drop_pg_vector_table(sender, instance, **kwargs):
    if instance.full_table_name:
        drop_vector_table(instance.full_table_name)
