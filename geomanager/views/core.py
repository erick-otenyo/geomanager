from rest_framework.decorators import api_view
from rest_framework.response import Response

from geomanager.models import Category, TileGlStyle
from geomanager.models.core import GeomanagerSettings
from geomanager.serializers import CategorySerializer
from geomanager.utils.countries import get_country_info


@api_view(['GET'])
def get_mapviewer_config(request):
    categories = Category.objects.all()
    categories_data = CategorySerializer(categories, many=True).data

    response = {
        "categories": categories_data
    }

    settings = GeomanagerSettings.for_request(request)

    if settings.country:
        country_iso = settings.country.alpha3
        country_data = {
            "iso": country_iso
        }
        country_info = get_country_info(country_iso)
        if country_info:
            country_data.update(**country_info)
        country_data.update({"name": settings.country.name})

        response.update({
            "country": country_data
        })

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
