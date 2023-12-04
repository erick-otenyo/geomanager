from asgiref.sync import async_to_sync
from django_nextjs.render import render_nextjs_page
from wagtail.api.v2.utils import get_full_url
from wagtailiconchooser.utils import get_svg_sprite_for_icons

from geomanager.models import GeomanagerSettings, Category
from geomanager.models.vector_file import get_legend_icons


def map_view(request, location_type=None, adm0=None, adm1=None, adm2=None):
    # get svg sprite for categories and legend icons
    category_icons = [category.icon for category in Category.objects.all()]
    legend_icons = get_legend_icons()
    icons = [*category_icons, *legend_icons]
    svg_sprite = get_svg_sprite_for_icons(icons)

    context = {
        "svg_sprite": svg_sprite,
    }

    return async_to_sync(render_nextjs_page)(request, "django_nextjs/mapviewer.html", context, allow_redirects=True)
