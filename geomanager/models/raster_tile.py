from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel

from geomanager.models.core import Dataset
from geomanager.models.tile_base import BaseTileLayer


class RasterTileLayer(BaseTileLayer):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="raster_tile_layers",
                                verbose_name=_("dataset"))

    class Meta:
        verbose_name = _("Raster Tile Layer")
        verbose_name_plural = _("Raster Tile Layers")

    panels = [
        FieldPanel("dataset"),
        *BaseTileLayer.panels,
    ]

    def __str__(self):
        return self.title

    @property
    def layer_config(self):
        tile_url = self.tile_url

        layer_config = {
            "type": "raster",
            "source": {
                "type": "raster",
                "tiles": [tile_url]
            }
        }

        return layer_config
