import json

from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from wagtail.admin.auth import (
    user_passes_test,
    user_has_any_page_permission
)
from wagtail.api.v2.utils import get_full_url
from wagtail_modeladmin.helpers import AdminURLHelper

from geomanager.models import (
    Dataset, Category
)
from geomanager.models.vector_tile import VectorTileLayer, VectorTileLayerIcon
from geomanager.serializers.vector_tile import VectorTileLayerSerializer
from geomanager.utils import UUIDEncoder


@user_passes_test(user_has_any_page_permission)
def preview_vector_tile_layers(request, dataset_id, layer_id=None):
    dataset = get_object_or_404(Dataset, pk=dataset_id)

    category_admin_helper = AdminURLHelper(Category)
    categories_url = category_admin_helper.get_action_url("index")

    dataset_admin_helper = AdminURLHelper(Dataset)
    dataset_list_url = dataset_admin_helper.get_action_url("index") + f"?id={dataset_id}"

    vector_tile_layer_admin_helper = AdminURLHelper(VectorTileLayer)
    vector_tile_layer_list_url = vector_tile_layer_admin_helper.get_action_url("index")
    vector_tile_layer_list_url = vector_tile_layer_list_url + f"?dataset__id__exact={dataset_id}"

    layer = None
    if layer_id:
        layer = VectorTileLayer.objects.get(pk=layer_id)

    dataset_layers = VectorTileLayerSerializer(dataset.vector_tile_layers, many=True).data

    # get icon images for the dataset vector tile layers, if any
    icon_images = []
    layers_id = [layer.get("id") for layer in dataset_layers]
    for icon in VectorTileLayerIcon.objects.filter(layer__in=layers_id):
        icon_images.append({"name": icon.name, "url": get_full_url(request, icon.file.url)})

    navigation_items = [
        {"url": categories_url, "label": Category._meta.verbose_name_plural},
        {"url": dataset_list_url, "label": Dataset._meta.verbose_name_plural},
        {"url": vector_tile_layer_list_url, "label": VectorTileLayer._meta.verbose_name_plural},
        {"url": "#", "label": _("Preview")},
    ]

    context = {
        "dataset": dataset,
        "selected_layer": layer,
        "datasets_index_url": dataset_list_url,
        "vector_tile_layer_list_url": vector_tile_layer_list_url,
        "dataset_layers": json.dumps(dataset_layers, cls=UUIDEncoder),
        "icon_images": icon_images,
        "navigation_items": navigation_items,
    }

    return render(request, 'geomanager/vector_tile/vector_tile_layer_preview.html', context)
