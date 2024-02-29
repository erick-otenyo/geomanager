from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail.api.v2.utils import get_full_url
from wagtail.fields import StreamField

from geomanager.blocks import FillVectorLayerBlock, LineVectorLayerBlock
from geomanager.fields import ListField
from geomanager.settings import geomanager_settings
from geomanager.utils.tiles import get_vector_render_layers
from geomanager.utils.vector_utils import drop_vector_table


class AdditionalMapBoundaryData(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Dataset Name"))
    table_name = models.CharField(max_length=256, unique=True)

    properties = models.JSONField()
    geometry_type = models.CharField(max_length=100)
    bounds = ListField(max_length=256)
    active = models.BooleanField(default=True, verbose_name=_("Active"))

    render_layers = StreamField([
        ("fill", FillVectorLayerBlock(label=_("Polygon Layer"))),
        ("line", LineVectorLayerBlock(label=_("Line Layer"))),
    ], use_json_field=True, null=True, blank=True, min_num=1, verbose_name=_("Map Layers"))

    class Meta:
        verbose_name = _("Additional Map Boundary Dataset")
        verbose_name_plural = _("Additional Map Boundary Datasets")

    def __str__(self):
        return self.name

    @property
    def tiles_url(self):
        tiles_url = reverse("map_boundary_tiles", args=(self.table_name, 0, 0, 0)).replace("/0/0/0", r"/{z}/{x}/{y}")
        return tiles_url

    @property
    def columns(self):
        if not self.properties:
            return []
        if self.properties:
            return [c.get("name") for c in self.properties]

    @property
    def full_table_name(self):
        pg_service_schema = geomanager_settings.get("vector_db_schema")
        return f"{pg_service_schema}.{self.table_name}"

    def get_dataset_config(self, request=None):
        dataset_id = f"{self.table_name}-{self.pk}"
        tiles_url = get_full_url(request, self.tiles_url)

        render_layers = get_vector_render_layers(self.render_layers)

        dataset_config = {
            "id": dataset_id,
            "dataset": dataset_id,
            "name": self.name,
            "layer": dataset_id,
            "isBoundary": True,
            "public": True,
            "layers": [
                {
                    "id": dataset_id,
                    "isBoundary": True,
                    "analysisEndpoint": "use",
                    "tableName": self.table_name,
                    "name": self.name,
                    "default": True,
                    "layerConfig": {
                        "type": "vector",
                        "source": {
                            "type": "vector",
                            "tiles": [tiles_url],
                        },
                        "render": {
                            "layers": render_layers
                        }
                    },
                    "interactionConfig": {
                        "output": [
                            {
                                "column": "gid",
                                "property": "ID",
                                'type': "string",
                            },
                        ]
                    }
                }
            ]
        }

        return dataset_config


@receiver(pre_delete, sender=AdditionalMapBoundaryData)
def drop_pg_vector_table(sender, instance, **kwargs):
    if instance.table_name:
        drop_vector_table(instance.table_name)
