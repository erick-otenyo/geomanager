from django.utils.decorators import method_decorator
from wagtail.models import Page
from wagtailcache.cache import cache_page

from geomanager.models import AbstractStationsPage


@method_decorator(cache_page, name="serve")
class HomePage(Page):
    pass


class StationsPage(AbstractStationsPage):
    parent_page_types = ["home.HomePage"]
    template = "stations/stations_page.html"

    content_panels = Page.content_panels
