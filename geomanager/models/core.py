import base64
import json
import uuid

from django.db import models
from django.urls.base import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from treebeard.mp_tree import MP_Node
from wagtail import blocks
from wagtail.admin.panels import (
    FieldPanel,
    TabbedInterface,
    ObjectList
)
from wagtail.api.v2.utils import get_full_url
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.fields import StreamField, RichTextField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page, CollectionManager
from wagtail_adminsortable.models import AdminSortable
from wagtail_modeladmin.helpers import AdminURLHelper
from wagtailiconchooser.widgets import IconChooserWidget

from geomanager.helpers import (
    get_layer_action_url,
    get_preview_url,
    get_upload_url
)
from .tile_gl import MBTSource
from ..blocks import NavigationItemsBlock
from ..forms import CategoryForm
from ..utils import UUIDEncoder

DEFAULT_RASTER_MAX_UPLOAD_SIZE_MB = 100


class Category(TimeStampedModel, AdminSortable, ClusterableModel, MP_Node):
    base_form_class = CategoryForm

    title = models.CharField(max_length=16, verbose_name=_("title"), help_text=_("Title of the category"))
    icon = models.CharField(max_length=255, verbose_name=_("icon"), blank=True, null=True)
    active = models.BooleanField(default=True, verbose_name=_("active"), help_text=_("Is the category active ?"))
    public = models.BooleanField(default=True, verbose_name=_("public"), help_text=_("Is the category public ?"))

    objects = CollectionManager()
    # Tell treebeard to order Collections' paths such that they are ordered by name at each level.
    node_order_by = ["order"]

    class Meta(AdminSortable.Meta):
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["path", "order"]

    def __str__(self):
        return self.title

    panels = [
        FieldPanel("title"),
        FieldPanel("icon", widget=IconChooserWidget),
        FieldPanel("active"),
        FieldPanel("public"),
        FieldPanel("parent"),

        # InlinePanel("sub_categories", heading=_("Sub Categories"), label=_("Sub Category")),
    ]

    def get_ancestors(self, inclusive=False):
        return Category.objects.ancestor_of(self, inclusive)

    def get_descendants(self, inclusive=False):
        return Category.objects.descendant_of(self, inclusive)

    def get_siblings(self, inclusive=True):
        return Category.objects.sibling_of(self, inclusive)

    def get_next_siblings(self, inclusive=False):
        return self.get_siblings(inclusive).filter(path__gte=self.path).order_by("path")

    def get_prev_siblings(self, inclusive=False):
        return (
            self.get_siblings(inclusive).filter(path__lte=self.path).order_by("-path")
        )

    def get_indented_name(self, indentation_start_depth=2, html=True):
        """
        Renders this Category's title as a formatted string that displays its hierarchical depth via indentation.
        If indentation_start_depth is supplied, the Category's depth is rendered relative to that depth.
        indentation_start_depth defaults to 2, the depth of the first non-Root Category.
        Pass html=False to get a plain-text, instead of the default HTML.

        Example text output: "    ↳ Rainfall"
        Example HTML output: "&nbsp;&nbsp;&nbsp;&nbsp;&#x21b3 Pies"
        """
        display_depth = self.depth - indentation_start_depth

        icon = self.icon or "layer-group"

        # A Category with a display depth of 0 or less (Root's can be -1), should have no indent.
        if display_depth <= 0:
            if html:
                return format_html(
                    "{svg_icon} {name}",
                    svg_icon=mark_safe(f""" 
                            <span class="icon-wrapper">
                                <svg class="icon icon-{icon} icon" aria-hidden="true" style="height:20px;width:20px">
                                    <use href="#icon-{icon}"></use>
                                </svg>
                            </span>"""),
                    name=self.title,
                )

            return self.title

        # Indent each level of depth by 4 spaces (the width of the ↳ character in our admin font), then add ↳
        # before adding the name.
        if html:
            # NOTE: &#x21b3 is the hex HTML entity for ↳.
            return format_html(
                "{indent}{icon} {svg_icon} {name}",
                indent=mark_safe("&nbsp;" * 4 * display_depth),
                icon=mark_safe("&#x21b3"),
                svg_icon=mark_safe(f""" 
                        <span class="icon-wrapper">
                            <svg class="icon icon-{icon} icon" aria-hidden="true" style="height:20px;width:20px">
                                <use href="#icon-{icon}"></use>
                            </svg>
                        </span>"""),
                name=self.title,
            )
        # Output unicode plain-text version
        return "{}↳ {}".format(" " * 4 * display_depth, self.title)

    def datasets_list_url(self):
        dataset_admin_helper = AdminURLHelper(Dataset)
        dataset_index_url = dataset_admin_helper.get_action_url("index")
        return dataset_index_url + f"?category__id__exact={self.pk}"

    def dataset_create_url(self):
        dataset_admin_helper = AdminURLHelper(Dataset)
        dataset_create_url = dataset_admin_helper.get_action_url("create")
        return dataset_create_url + f"?category_id={self.pk}"

    @property
    def mapviewer_map_url(self):
        base_mapviewer_url = reverse("mapview")

        map_config = {
            "datasets": [{"dataset": "political-boundaries", "layers": ["political-boundaries"], "visibility": True}]
        }

        map_str = json.dumps(map_config, separators=(',', ':'))

        map_bytes = map_str.encode()
        map_base64_bytes = base64.b64encode(map_bytes)
        map_byte_str = map_base64_bytes.decode()

        menu_config = {"menuSection": "datasets", "datasetCategory": self.title}
        menu_str = json.dumps(menu_config, separators=(',', ':'))
        menu_bytes = menu_str.encode()
        menu_base64_bytes = base64.b64encode(menu_bytes)
        menu_byte_str = menu_base64_bytes.decode()

        return base_mapviewer_url + f"?map={map_byte_str}&mapMenu={menu_byte_str}"


class SubCategory(Orderable):
    category = ParentalKey(Category, on_delete=models.CASCADE, related_name="sub_categories")
    title = models.CharField(max_length=256, verbose_name=_("title"))
    active = models.BooleanField(default=True, verbose_name=_("active"))
    public = models.BooleanField(default=True, verbose_name=_("public"))

    class Meta:
        verbose_name = _("Subcategory")
        verbose_name_plural = _("Subcategories")

    panels = [
        FieldPanel("title"),
        FieldPanel("active"),
        FieldPanel("public"),
    ]

    def __str__(self):
        return self.title

    def __str__(self):
        return self.title


class Dataset(TimeStampedModel, AdminSortable):
    DATASET_TYPE_CHOICES = (
        ("raster_file", _("Raster File - NetCDF/GeoTiff")),
        ("vector_file", _("Vector File - Shapefile, Geojson")),
        ("wms", _("Web Map Service - WMS Layer")),
        ("raster_tile", _("XYZ Raster Tile Layer")),
        ("vector_tile", _("XYZ Vector Tile Layer")),
    )

    CURRENT_TIME_METHOD_CHOICES = (
        ("latest_from_source", _("Latest available date from source")),
        ("earliest_from_source", _("Earliest available date from source")),
        ("previous_to_now", _("Date previous to current date time")),
        ("next_to_now", _("Date next to current date time")),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_("title"),
                             help_text=_("The Dataset title as will appear to the public"))
    category = models.ForeignKey(Category, verbose_name=_("category"), on_delete=models.PROTECT,
                                 related_name="datasets")
    sub_category = models.ForeignKey(SubCategory, verbose_name=_("Subcategory"), on_delete=models.PROTECT)
    summary = models.CharField(max_length=100, null=True, blank=True,
                               verbose_name=_("summary"),
                               help_text=_("Short summary of less than 100 characters"))
    metadata = models.ForeignKey("Metadata", verbose_name=_("metadata"), null=True, blank=True,
                                 on_delete=models.SET_NULL)
    layer_type = models.CharField(max_length=100, choices=DATASET_TYPE_CHOICES, default="raster_file",
                                  verbose_name=_("Layer type"))
    published = models.BooleanField(default=True, verbose_name=_("published"),
                                    help_text=_("Should the dataset be available for visualization ?"
                                                " If unchecked, the dataset is assumed to be in draft mode "
                                                "and thus not ready"))
    public = models.BooleanField(default=True, verbose_name=_("public"),
                                 help_text=_("Should the dataset be visible to everyone ?"
                                             " If unchecked, only authorized users can view"))
    initial_visible = models.BooleanField(default=False, verbose_name=_("Initially visible on Map by default"),
                                          help_text=_("Make the dataset visible on the map by default"))

    multi_temporal = models.BooleanField(default=True, verbose_name=_("Multi-temporal"),
                                         help_text=_("The dataset is multi-temporal"), )

    multi_layer = models.BooleanField(default=False, verbose_name=_("Multi-layer"),
                                      help_text=_("The dataset has more than one layer, to be displayed together"), )
    enable_all_multi_layers_on_add = models.BooleanField(default=True,
                                                         verbose_name=_("Enable all Multi-Layers when adding to map"),
                                                         help_text=_("Enable all Multi-Layers at once when adding "
                                                                     "the dataset to the map"), )
    near_realtime = models.BooleanField(default=False, verbose_name=_("Near realtime"),
                                        help_text=_(
                                            "Is the layer near realtime?, for example updates every 10 minutes"))

    current_time_method = models.CharField(max_length=100, choices=CURRENT_TIME_METHOD_CHOICES,
                                           default="latest_from_source",
                                           verbose_name=_("current time method"),
                                           help_text=_(
                                               "How to pick default time and for updates, for Multi-Temporal data"))
    auto_update_interval = models.IntegerField(blank=True, null=True, verbose_name=_("Auto Update interval in minutes"),
                                               help_text=_(
                                                   "After how many minutes should the layer auto update on the map to "
                                                   "show current data, if multi-temporal. Leave empty to"
                                                   " disable auto updating"))

    can_clip = models.BooleanField(default=True, verbose_name=_("Enable Clipping by shape"),
                                   help_text=_("Check to enable clipping by boundary or drawn shapes, "
                                               "for raster and vector datasets. Not implemented for WMS types"))

    class Meta(AdminSortable.Meta):
        verbose_name = _("Dataset")
        verbose_name_plural = _("Datasets")

    panels = [
        FieldPanel("title"),
        FieldPanel("category"),
        FieldPanel("sub_category"),
        FieldPanel("layer_type"),
        FieldPanel("summary"),
        FieldPanel("metadata"),
        FieldPanel("published"),
        FieldPanel("public"),
        FieldPanel("initial_visible"),
        FieldPanel("multi_temporal"),
        FieldPanel("multi_layer"),
        FieldPanel("enable_all_multi_layers_on_add"),
        FieldPanel("near_realtime"),
        FieldPanel("current_time_method"),
        FieldPanel("auto_update_interval"),
        FieldPanel("can_clip"),
    ]

    def __str__(self):
        return self.title

    @property
    def mapviewer_map_url(self):
        base_mapviewer_url = reverse("mapview")

        layers = []

        layer = self.layers.first()

        if layer:
            layers.append(layer.pk)

        map_config = {
            "datasets": [
                {"dataset": self.pk, "visibility": True, "layers": layers},
                {"dataset": "political-boundaries", "layers": ["political-boundaries"], "visibility": True}]
        }

        map_str = json.dumps(map_config, cls=UUIDEncoder, separators=(',', ':'))

        map_bytes = map_str.encode()
        map_base64_bytes = base64.b64encode(map_bytes)
        map_byte_str = map_base64_bytes.decode()

        menu_config = {"menuSection": "datasets", "datasetCategory": self.category.title}
        menu_str = json.dumps(menu_config, separators=(',', ':'))
        menu_bytes = menu_str.encode()
        menu_base64_bytes = base64.b64encode(menu_bytes)
        menu_byte_str = menu_base64_bytes.decode()

        return base_mapviewer_url + f"?map={map_byte_str}&mapMenu={menu_byte_str}"

    @property
    def auto_update_interval_milliseconds(self):
        if self.auto_update_interval:
            return self.auto_update_interval * 60000
        return None

    @property
    def capabilities(self):
        caps = []
        if self.multi_temporal:
            caps.append("timeseries")
        if self.near_realtime:
            caps.append("nearRealTime")
        return caps

    def dataset_url(self):
        admin_helper = AdminURLHelper(self)
        admin_edit_url = admin_helper.get_action_url("index", self.pk)
        return admin_edit_url + f"?id={self.pk}"

    def get_layers_rel(self):
        layer_type = self.layer_type

        if layer_type == "raster_file":
            return self.raster_file_layers

        if layer_type == "vector_file":
            return self.vector_file_layers

        if layer_type == "wms":
            return self.wms_layers

        if layer_type == "raster_tile":
            return self.raster_tile_layers

        if layer_type == "vector_tile":
            return self.vector_tile_layers

        return None

    @property
    def category_url(self):
        if self.category:
            category_admin_helper = AdminURLHelper(Category)
            category_edit_url = category_admin_helper.get_action_url("edit", self.category.pk)
            return category_edit_url
        return None

    @property
    def upload_url(self):
        return get_upload_url(self.layer_type, self.pk)

    def layers_list_url(self):
        list_layer_url = get_layer_action_url(self.layer_type, "index")

        if list_layer_url:
            list_layer_url = list_layer_url + f"?dataset__id__exact={self.pk}"

        return list_layer_url

    def create_layer_url(self):
        if self.has_layers() and not self.multi_layer:
            return None

        create_layer_url = get_layer_action_url(self.layer_type, "create")
        if create_layer_url:
            create_layer_url = create_layer_url + f"?dataset_id={self.pk}"

        return create_layer_url

    @property
    def preview_url(self):
        return get_preview_url(self.layer_type, self.pk)

    @property
    def layers(self):
        return self.get_layers_rel()

    def has_layers(self):
        layers = self.get_layers_rel()
        if layers:
            return layers.exists()

        return False

    def can_preview(self):
        layers_check = [
            self.has_raster_files(),
            self.has_vector_tables(),
            self.has_wms_layers(),
            self.has_raster_tile_layers(),
            self.has_vector_tile_layers()
        ]

        return any(layers_check)

    def has_raster_files(self):
        layers = self.raster_file_layers.all()
        has_raster_files = False
        if layers.exists():
            for layer in layers:
                if layer.raster_files.exists():
                    has_raster_files = True
                    break
        return has_raster_files

    def has_vector_tables(self):
        vector_layers = self.vector_file_layers.all()
        has_vector_tables = False
        if vector_layers.exists():
            for layer in vector_layers:
                if layer.vector_tables.all().exists():
                    has_vector_tables = True
                    break
        return has_vector_tables

    def has_wms_layers(self):
        return self.wms_layers.exists()

    def has_raster_tile_layers(self):
        return self.raster_tile_layers.exists()

    def has_vector_tile_layers(self):
        return self.vector_tile_layers.exists()

    def get_default_layer(self):
        layers = self.get_layers_rel()

        if layers and layers.exists():
            default = layers.filter(default=True)
            if default.exists():
                return default.first().pk
            else:
                return layers.first().pk

        return None

    def get_wms_layers_json(self):
        return []


class Metadata(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_("title"), help_text=_("Title of the dataset"))
    subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("subtitle"),
                                help_text=_("Subtitle if any"))
    function = models.TextField(max_length=255, blank=True, null=True, verbose_name=_("Dataset summary"),
                                help_text=_("Short summary of what the dataset shows. Keep it short."))
    resolution = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("resolution"),
                                  help_text=_("The Spatial resolution of the dataset, for example 10km by 10 km"))
    geographic_coverage = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Geographic coverage"),
                                           help_text=_("The geographic coverage of the dataset. For example East Africa"
                                                       " or specific country name like Ethiopia, or Africa"))
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("source"),
                              help_text=_("The source of the data where was it generated or produced"))
    license = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("license"),
                               help_text=_("Any licensing information for the dataset"))
    frequency_of_update = models.CharField(max_length=255, blank=True, null=True,
                                           verbose_name=_("Frequency of updates"),
                                           help_text=_("How frequent is the dataset updated. "
                                                       "For example daily, weekly, monthly etc"))
    overview = RichTextField(blank=True, null=True, verbose_name=_("detail"),
                             help_text=_("Detail description of the dataset, including the methodology, "
                                         "references or any other relevant information"))
    cautions = RichTextField(blank=True, null=True, verbose_name=_("cautions"),
                             help_text=_("What things should users be aware as they use and interpret this dataset"))
    citation = RichTextField(blank=True, null=True, verbose_name=_("citation"),
                             help_text=_("Scientific citation for this dataset if any. "
                                         "For example the citation for a scientific paper for the dataset"))
    download_data = models.URLField(blank=True, null=True, verbose_name=_("Data download link"),
                                    help_text=_("External link to where the source data can be found and downloaded"))
    learn_more = models.URLField(blank=True, null=True, verbose_name=_("Learn more link"),
                                 help_text=_("External link to where more detail about the dataset can be found"))

    class Meta:
        verbose_name = _("Metadata")
        verbose_name_plural = _("Metadata")

    def __str__(self):
        return self.title


def get_styles():
    from geomanager.models import MBTSource
    return [(style.id, style.name) for style in MBTSource.objects.all()]


class BaseLayer(AdminSortable, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_("title"), help_text=_("Layer title"))
    default = models.BooleanField(default=False, verbose_name=_("default"), help_text=_("Is Default Layer"))

    @property
    def linked_layers(self):
        is_multi_layer = self.dataset.multi_layer

        if is_multi_layer:
            return [str(layer.pk) for layer in self.dataset.layers.exclude(pk=self.pk)]
        return []

    @property
    def edit_url(self):
        edit_url = get_layer_action_url(layer_type=self.dataset.layer_type, action="edit", action_args=self.pk)
        return edit_url

    @property
    def upload_url(self):
        return get_upload_url(layer_type=self.dataset.layer_type, dataset_id=self.dataset.pk, layer_id=self.pk)

    @property
    def preview_url(self):
        return get_preview_url(layer_type=self.dataset.layer_type, dataset_id=self.dataset.pk, layer_id=self.pk)

    @property
    def mapviewer_map_url(self):
        base_mapviewer_url = reverse("mapview")

        map_config = {
            "datasets": [
                {"dataset": self.dataset.pk, "visibility": True, "layers": [self.pk]},
                {"dataset": "political-boundaries", "layers": ["political-boundaries"], "visibility": True}
            ]
        }

        map_str = json.dumps(map_config, cls=UUIDEncoder, separators=(',', ':'))

        map_bytes = map_str.encode()
        map_base64_bytes = base64.b64encode(map_bytes)
        map_byte_str = map_base64_bytes.decode()

        menu_config = {"menuSection": "datasets", "datasetCategory": self.dataset.category.title}
        menu_str = json.dumps(menu_config, separators=(',', ':'))
        menu_bytes = menu_str.encode()
        menu_base64_bytes = base64.b64encode(menu_bytes)
        menu_byte_str = menu_base64_bytes.decode()

        return base_mapviewer_url + f"?map={map_byte_str}&mapMenu={menu_byte_str}"

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.dataset.multi_layer:
            if self.default:
                self.dataset.layers.filter(default=True).exclude(pk=self.pk).update(default=False)
            else:
                if not self.dataset.layers.filter(default=True).exclude(pk=self.pk).exists():
                    self.default = True
                    self.dataset.layers.filter(default=True).exclude(pk=self.pk).update(default=False)

        super().save(*args, **kwargs)


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
