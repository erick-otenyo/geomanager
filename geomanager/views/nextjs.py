from django_nextjs.render import render_nextjs_page_sync
from wagtailcache.cache import nocache_page
from wagtailiconchooser.utils import get_svg_sprite_for_icons

from geomanager.models import GeomanagerSettings, Category
from geomanager.models.vector_file import get_legend_icons


@nocache_page
def map_view(request, location_type=None, adm0=None, adm1=None, adm2=None):
    # get svg sprite for categories and legend icons
    category_icons = [category.icon for category in Category.objects.all()]
    legend_icons = get_legend_icons()
    icons = [*category_icons, *legend_icons]
    svg_sprite = get_svg_sprite_for_icons(icons)

    gm_settings = GeomanagerSettings.for_request(request)
    context = {
        "svg_sprite": svg_sprite,
        "logo": gm_settings.logo,
        "logo_url": request.build_absolute_uri("/")
    }

    if gm_settings.logo_page:
        context.update({"logo_url": request.build_absolute_uri(gm_settings.logo_page.url)})

    if not gm_settings.logo_page and gm_settings.logo_external_link:
        context.update({"logo_url": gm_settings.logo_external_link, "logo_url_external": True})

    for block in gm_settings.navigation:
        if block.block_type == "menu_items":
            context.update({"menu_items": block.value})

    return render_nextjs_page_sync(request, template_name="django_nextjs/mapviewer.html", context=context,
                                   allow_redirects=True)
