import json

from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from wagtail.admin.auth import (
    user_passes_test,
    user_has_any_page_permission
)
from wagtail_modeladmin.helpers import AdminURLHelper

from geomanager.models import (
    Dataset, Category
)
from geomanager.models.raster_tile import RasterTileLayer
from geomanager.serializers.raster_tile import RasterTileLayerSerializer
from geomanager.utils import UUIDEncoder


@user_passes_test(user_has_any_page_permission)
def preview_raster_tile_layers(request, dataset_id, layer_id=None):
    dataset = get_object_or_404(Dataset, pk=dataset_id)

    category_admin_helper = AdminURLHelper(Category)
    categories_url = category_admin_helper.get_action_url("index")

    dataset_admin_helper = AdminURLHelper(Dataset)
    dataset_list_url = dataset_admin_helper.get_action_url("index") + f"?id={dataset_id}"

    raster_tile_layer_admin_helper = AdminURLHelper(RasterTileLayer)
    raster_tile_layer_list_url = raster_tile_layer_admin_helper.get_action_url("index")
    raster_tile_layer_list_url = raster_tile_layer_list_url + f"?dataset__id__exact={dataset_id}"

    layer = None
    if layer_id:
        layer = RasterTileLayer.objects.get(pk=layer_id)

    dataset_layers = RasterTileLayerSerializer(dataset.raster_tile_layers, many=True).data

    navigation_items = [
        {"url": categories_url, "label": Category._meta.verbose_name_plural},
        {"url": dataset_list_url, "label": Dataset._meta.verbose_name_plural},
        {"url": raster_tile_layer_list_url, "label": RasterTileLayer._meta.verbose_name_plural},
        {"url": "#", "label": _("Preview")},
    ]

    context = {
        "dataset": dataset,
        "selected_layer": layer,
        "datasets_index_url": dataset_list_url,
        "raster_tile_layer_list_url": raster_tile_layer_list_url,
        "dataset_layers": json.dumps(dataset_layers, cls=UUIDEncoder),
        "navigation_items": navigation_items,
    }

    return render(request, 'geomanager/raster_tile/raster_tile_layer_preview.html', context)
