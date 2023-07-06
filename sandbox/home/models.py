from django.utils.decorators import method_decorator
from wagtail.models import Page
from wagtailcache.cache import cache_page


@method_decorator(cache_page, name="serve")
class HomePage(Page):
    pass
