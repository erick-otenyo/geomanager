from django_nextjs.render import render_nextjs_page_sync
from wagtail.admin.views import home

from geomanager.models import GeomanagerSettings


def map_view(request, location_type=None, adm0=None, adm1=None, adm2=None):
    svg_sprite = str(home.sprite(None).content, "utf-8")

    print(request.path, "HELLOOOOO")

    gm_settings = GeomanagerSettings.for_request(request)
    context = {
        "svg_sprite": svg_sprite,
        "logo": gm_settings.logo,
    }

    for block in gm_settings.navigation:
        if block.block_type == "menu_items":
            context.update({"menu_items": block.value})

    return render_nextjs_page_sync(request, template_name="django_nextjs/mapviewer.html", context=context)
