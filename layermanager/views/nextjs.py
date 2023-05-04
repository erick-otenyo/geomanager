from django_nextjs.render import render_nextjs_page_sync
from wagtail.admin.views import home


def map_view(request, location_type=None, adm0=None, adm1=None, adm2=None):
    svg_sprite = str(home.sprite(None).content, "utf-8")
    return render_nextjs_page_sync(request, template_name="django_nextjs/mapviewer.html",
                                   context={"svg_sprite": svg_sprite})
