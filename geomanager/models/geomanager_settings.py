from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.panels import (
    FieldPanel,
    TabbedInterface,
    ObjectList
)
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Page

from geomanager.blocks import NavigationItemsBlock
from .tile_gl import MBTSource

DEFAULT_RASTER_MAX_UPLOAD_SIZE_MB = 100


@register_setting
class GeomanagerSettings(BaseSiteSetting):
    max_upload_size_mb = models.IntegerField(default=DEFAULT_RASTER_MAX_UPLOAD_SIZE_MB,
                                             verbose_name=_("Maximum upload size in MegaBytes"),
                                             help_text=_(
                                                 "Maximum raster file size that can be uploaded in MegaBytes. "
                                                 "Default is 100Mbs."))
    crop_raster_to_country = models.BooleanField(default=True, verbose_name=_("Crop raster to country"),
                                                 help_text=_("Crop the uploaded raster file to the country boundaries"))

    tile_gl_fonts_url = models.URLField(max_length=256,
                                        default="https://fonts.openmaptiles.org/{fontstack}/{range}.pbf",
                                        verbose_name=_("GL Styles Font Url"),
                                        help_text=_("GL Styles Font Url"))
    tile_gl_source = models.ForeignKey(MBTSource, blank=True, null=True, on_delete=models.SET_NULL,
                                       verbose_name=_("Open Map Tiles Source"))
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Logo")
    )
    logo_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Logo page"),
        help_text=_("Internal page to navigate to on clicking the logo")
    )
    logo_external_link = models.URLField(max_length=255, null=True, blank=True,
                                         verbose_name=_("Logo external link"),
                                         help_text=_("Used if internal logo page not provided"))
    terms_of_service_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Terms of Service Page"),
        help_text=_("MapViewer Terms of Service page")
    )
    privacy_policy_page = models.ForeignKey(
        Page,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_("Privacy Policy Page"),
        help_text=_("MapViewer Privacy Policy Page")
    )

    navigation = StreamField([
        ('menu_items', blocks.ListBlock(NavigationItemsBlock(max_num=8))),
    ], block_counts={
        'menu_items': {'max_num': 1},
    }, use_json_field=True, null=True, blank=True)

    base_maps = StreamField([
        ('basemap', blocks.StructBlock([
            ('label', blocks.CharBlock(label=_("label"))),
            ('backgroundColor', blocks.CharBlock(label=_("background color"))),
            ('image', ImageChooserBlock(required=False, label=_("image"))),
            ('basemapGroup', blocks.CharBlock(label=_("basemap group"))),
            ('labelsGroup', blocks.CharBlock(label=_("labels group"))),
            ('url', blocks.URLBlock(required=False, label=_("url"))),
            ('default', blocks.BooleanBlock(required=False, label=_("default"), help_text=_("Is default style ?"))),
        ]))
    ], use_json_field=True, null=True, blank=True)

    class Meta:
        verbose_name = _("Geomanager Settings")

    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("max_upload_size_mb"),
            FieldPanel("crop_raster_to_country"),
        ], heading=_("Upload Settings")),
        ObjectList([
            FieldPanel("tile_gl_fonts_url"),
            FieldPanel("tile_gl_source"),
            FieldPanel("base_maps"),
        ], heading=_("Basemap TileServer Settings")),
        ObjectList([
            FieldPanel("logo"),
            FieldPanel("logo_page"),
            FieldPanel("logo_external_link"),
            FieldPanel("terms_of_service_page"),
            FieldPanel("privacy_policy_page"),
            FieldPanel("navigation"),
        ], heading=_("Navigation Settings")),
    ])

    @property
    def max_upload_size_bytes(self):
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def logo_link(self):
        if self.logo_page:
            return get_full_url(None, self.logo_page.url)

        if self.logo_external_link:
            return self.logo_external_link

        return "/"