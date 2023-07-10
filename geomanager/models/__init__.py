import logging

from django.db.models.signals import post_save
from wagtailcache.cache import clear_cache

from .core import *
from .raster import *
from .tile_gl import *
from .vector import *
from .profile import *
from .aoi import *
from .stations import *

logger = logging.getLogger(__name__)


# clear wagtail cache on saving the following models
@receiver(post_save, sender=Category)
@receiver(post_save, sender=SubCategory)
@receiver(post_save, sender=Dataset)
@receiver(post_save, sender=Metadata)
@receiver(post_save, sender=GeomanagerSettings)
@receiver(post_save, sender=FileImageLayer)
@receiver(post_save, sender=LayerRasterFile)
@receiver(post_save, sender=RasterStyle)
@receiver(post_save, sender=WmsLayer)
@receiver(post_save, sender=MBTSource)
@receiver(post_save, sender=VectorLayer)
@receiver(post_save, sender=PgVectorTable)
def handle_clear_wagtail_cache(sender, **kwargs):
    logging.info("[WAGTAIL_CACHE]: Clearing cache")
    clear_cache()
