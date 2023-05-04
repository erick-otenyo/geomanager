from rest_framework.decorators import api_view
from rest_framework.response import Response

from layermanager.models import Category, TileGlStyle
from layermanager.models.core import LayerManagerSettings
from layermanager.serializers import CategorySerializer


@api_view(['GET'])
def get_mapviewer_config(request):
    categories = Category.objects.all()
    categories_data = CategorySerializer(categories, many=True).data

    response = {
        "categories": categories_data
    }

    settings = LayerManagerSettings.for_request(request)

    base_maps_data = []

    # get base maps
    for base_map in settings.base_maps:
        data = base_map.block.get_api_representation(base_map.value)
        for key, value in base_map.value.items():
            if key == "image" and value:
                data.update({"image": request.build_absolute_uri(value.file.url)})
            if key == "mapStyle" and value:
                style = TileGlStyle.objects.get(pk=value)
                data.update({"mapStyle": request.build_absolute_uri(style.map_style_url)})
        base_maps_data.append(data)

    response.update({"basemaps": base_maps_data})

    return Response(response)
