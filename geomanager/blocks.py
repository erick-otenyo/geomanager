from functools import cached_property

from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail_color_panel.blocks import NativeColorBlock
from wagtailiconchooser.blocks import IconChooserBlock


class NavigationItemsBlock(blocks.StructBlock):
    label = blocks.CharBlock(label=_("Label"))
    page = blocks.PageChooserBlock(required=False, label=_("Page"), help_text=_("Internal page to navigate"))
    external_link = blocks.URLBlock(required=False, label=_("External Link"),
                                    help_text=_("External link to navigate to. Used if internal page not provided"))


class QueryParamStaticBlock(blocks.StructBlock):
    key = blocks.CharBlock(label=_("Key"))
    value = blocks.CharBlock(label=_("Value"))


class QueryParamSelectableBlock(blocks.StructBlock):
    SELECTOR_TYPE_CHOICES = (
        ("radio", _("Radio")),
        ("dropdown", _("Dropdown")),
    )
    name = blocks.CharBlock(label=_("name"))
    label = blocks.CharBlock(required=False, label=_("label"))
    type = blocks.ChoiceBlock(choices=SELECTOR_TYPE_CHOICES, default="radio", label=_("Selector Type"))
    options = blocks.ListBlock(blocks.StructBlock([
        ('label', blocks.CharBlock(label=_("label"))),
        ('value', blocks.CharBlock(label=_("value"))),
        ('default', blocks.BooleanBlock(required=False, label=_("default"),
                                        help_text=_("Check to make default option")))]
    ), min_num=1, label=_("Options"))


class InlineLegendBlock(blocks.StructBlock):
    LEGEND_TYPES = (
        ("basic", _("Basic")),
        ("gradient", _("Gradient")),
        ("choropleth", _("Choropleth")),
    )
    type = blocks.ChoiceBlock(choices=LEGEND_TYPES, default="basic", label=_("Legend Type"))
    items = blocks.ListBlock(blocks.StructBlock([
        ('value', blocks.CharBlock(label=_("value"),
                                   help_text=_("Can be a number or text e.g '10' or '10-20' or 'Vegetation'"))),
        ('color', blocks.CharBlock(label=_("color"), help_text=_("Color value e.g rgb(73,73,73) or #494949"))),
    ]
    ), min_num=1, label=_("Legend Items"), )


class InlineIconLegendBlock(blocks.StructBlock):
    items = blocks.ListBlock(blocks.StructBlock([
        ('icon_image', IconChooserBlock(label=_("Icon Image"))),
        ('icon_label', blocks.CharBlock(label=_("Icon Label"), )),
        ('icon_color', NativeColorBlock(required=False, default="#000000", label=_("Icon color"))),
    ]
    ), min_num=1, label=_("Legend Icons"), )


# A filled polygon with an optional stroked border
class FillVectorLayerBlock(blocks.StructBlock):
    paint = blocks.StructBlock([
        ('fill_color', NativeColorBlock(required=False, default="#000000")),
        ('fill_opacity', blocks.FloatBlock(required=False, default=1.0,
                                           validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           )),
        ('fill_outline_color', NativeColorBlock(required=False, default="#000000")),
        ('fill_antialias', blocks.BooleanBlock(required=False, default=True)),
    ], label="Mapbox GL Paint Properties")

    filter = blocks.CharBlock(required=False)
    maxzoom = blocks.IntegerBlock(required=False)
    minzoom = blocks.IntegerBlock(required=False)


# A stroked line
class LineVectorLayerBlock(blocks.StructBlock):
    LINE_CAP_CHOICES = (
        ("butt", "Butt"),
        ("round", "Round"),
        ("square", "Square"),
    )

    LINE_JOIN_CHOICES = (
        ("miter", "Miter"),
        ("bevel", "Bevel"),
        ("round", "Round"),
    )

    paint = blocks.StructBlock([
        ('line_color', NativeColorBlock(required=False, default="#000000")),
        ('line_dasharray', blocks.CharBlock(required=False)),
        ('line_gap_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0, )),
        ('line_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           default=1.0)),
        ('line_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=1.0, )),
        ('line_offset', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0)),

        # Not implemented here
        # line-gradient - reason => requires source to be geojson, but our source is vector tiles
        # line-pattern
        # line-translate
        # line-translate-anchor
        # line-trim-offset

    ], label="Mapbox GL Paint Properties")

    layout = blocks.StructBlock([
        ('line_cap', blocks.ChoiceBlock(required=False, choices=LINE_CAP_CHOICES, default="butt")),
        ('line_join', blocks.ChoiceBlock(required=False, choices=LINE_JOIN_CHOICES, default="miter")),
        ('line_miter_limit', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=2.0)),
        ('line_round_limit', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=1.05)),
        # Note implemented here
        # line-sort-key
    ], label="Mapbox GL Layout Properties")

    filter = blocks.CharBlock(required=False)
    maxzoom = blocks.IntegerBlock(required=False)
    minzoom = blocks.IntegerBlock(required=False)


SYMBOL_ANCHOR_CHOICES = (
    ("center", "Center"),
    ("left", "Left"),
    ("right", "Right"),
    ("top", "Top"),
    ("bottom", "Bottom"),
    ("top-left", "Top Left"),
    ("top-right", "Top Right"),
    ("bottom-left", "Bottom Left"),
    ("bottom-right", "Bottom Right"),
)

SYMBOL_ALIGNMENT_CHOICES = (
    ("auto", "Auto"),
    ("map", "Map"),
    ("viewport", "Viewport"),
)


# An icon
class IconVectorLayerBlock(blocks.StructBlock):
    ICON_TEXT_FIT_CHOICES = (
        ("none", "None"),
        ("width", "Width"),
        ("height", "Height"),
        ("both", "Both"),
    )

    layout = blocks.StructBlock([
        ('icon_image', IconChooserBlock(label=_("Icon Image"))),
        ('icon_allow_overlap', blocks.BooleanBlock(required=False, default=False)),
        ('icon_anchor', blocks.ChoiceBlock(required=False, choices=SYMBOL_ANCHOR_CHOICES, default="center")),
        ('icon_ignore_placement', blocks.BooleanBlock(required=False, default=False)),
        ('icon_keep_upright', blocks.BooleanBlock(required=False, default=False)),
        ('icon_offset', blocks.CharBlock(required=False)),
        ('icon_optional', blocks.BooleanBlock(required=False, default=False)),
        ('icon_padding', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=2.0)),
        ('icon_pitch_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto")),
        ('icon_rotate', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(360)],
                                            default=0)),
        ('icon_rotation_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto",
                                                       )),
        ('icon_size', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                        default=1)),
        ('icon_text_fit', blocks.ChoiceBlock(required=False, choices=ICON_TEXT_FIT_CHOICES, default="none")),

        # Not implemented yet
        # icon-text-fit-padding
        # symbol-avoid-edges

    ], label="Mapbox GL Layout Properties")

    paint = blocks.StructBlock([
        ('icon_color', NativeColorBlock(required=False, default="#000000")),
        ('icon_halo_blur', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0)),
        ('icon_halo_color', NativeColorBlock(required=False, default="#000000")),
        ('icon_halo_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0)),
        ('icon_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           default=1.0)),

        # Not implemented yet
        # icon-translate
        # icon-translate-anchor

    ], label="Mapbox GL Paint Properties")


# Text label
class TextVectorLayerBlock(blocks.StructBlock):
    TEXT_JUSTIFY_CHOICES = (
        ("center", "Center"),
        ("left", "Left"),
        ("right", "Right"),
        ("auto", "Auto"),
    )

    TEXT_TRANSFORM_CHOICES = (
        ("none", "None"),
        ("uppercase", "Uppercase"),
        ("lowercase", "Lowercase"),
    )

    TEXT_TRANSLATE_ANCHOR_CHOICES = (
        ("map", "Map"),
        ("viewport", "Viewport"),
    )

    TEXT_WRITING_MODE_CHOICES = (
        ("horizontal", "Horizontal"),
        ("vertical", "Vertical"),
    )

    SYMBOL_PLACEMENT_CHOICES = (
        ("point", "Point"),
        ("line", "Line"),
        ("line-center", "Line Center"),
    )

    paint = blocks.StructBlock([
        ('text_color', NativeColorBlock(required=False, default="#000000")),
        ('text_halo_blur', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0)),
        ('text_halo_color', NativeColorBlock(required=False, default="#000000")),
        ('text_halo_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0)),
        ('text_translate', blocks.CharBlock(required=False)),
        ('text_translate_anchor', blocks.ChoiceBlock(required=False, choices=TEXT_TRANSLATE_ANCHOR_CHOICES,
                                                     default="map")),
    ], label="Mapbox GL Paint Properties")

    layout = blocks.StructBlock([
        ('symbol_placement', blocks.ChoiceBlock(required=False, choices=SYMBOL_PLACEMENT_CHOICES, default="point")),
        ('text_allow_overlap', blocks.BooleanBlock(required=False, default=False)),
        ('text_anchor', blocks.ChoiceBlock(required=False, choices=SYMBOL_ANCHOR_CHOICES, default="center")),
        ('text_field', blocks.CharBlock(required=True)),
        ('text_size', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=16)),
        ('text_transform', blocks.ChoiceBlock(required=False, choices=TEXT_TRANSFORM_CHOICES, default="none")),
        ('text_ignore_placement', blocks.BooleanBlock(required=False, default=False)),
        ('text_justify', blocks.ChoiceBlock(required=False, choices=TEXT_JUSTIFY_CHOICES, default="center")),
        ('text_keep_upright', blocks.BooleanBlock(required=False, default=False)),
        ('text_letter_spacing', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0)),
        ('text_line_height', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=1.2)),
        ('text_max_angle', blocks.IntegerBlock(required=False,
                                               validators=[MinValueValidator(0), MaxValueValidator(360)], default=45)),
        ('text_max_width', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=10)),
        ('text_offset', blocks.CharBlock(required=False)),
        ('text_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           default=1.0)),
        ('text_padding', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=2)),
        ('text_pitch_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto")),
        ('text_radial_offset', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=0)),
        ('text_rotate', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(360)],
                                            default=0)),
        ('text_rotation_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES,
                                                       default="auto", )),
        ('text_variable_anchor', blocks.ChoiceBlock(required=False, choices=SYMBOL_ANCHOR_CHOICES)),

        # Not implemented yet
        # symbol-avoid-edges
        # symbol-sort-key
        # symbol-spacing
        # text-font - reason => we should control the fonts used
        # text-optional
        # text-writing-mode

    ], label="Mapbox GL Layout Properties")


# A filled circle
class CircleVectorLayerBlock(blocks.StructBlock):
    paint = blocks.StructBlock([
        ('circle_color', NativeColorBlock(required=False, default="#000000")),
        ('circle_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                             default=1.0)),
        ('circle_radius', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=5.0,
                                            label=_("circle radius"))),
        ('circle_stroke_color', NativeColorBlock(required=False, default="#000000")),
        ('circle_stroke_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0)),

    ], label="Mapbox GL Paint Properties")

    filter = blocks.CharBlock(required=False)
    maxzoom = blocks.IntegerBlock(required=False)
    minzoom = blocks.IntegerBlock(required=False)


TIMESERIES_CHART_TYPES = (
    ("lines", _("Line Chart")),
    ("bars", _("Bar Chart")),
)


class FileLayerPointAnalysisBlock(blocks.StructBlock):
    instance_data_enabled = blocks.BooleanBlock(required=False, default=True, label=_("Show data for point"))
    timeseries_data_enabled = blocks.BooleanBlock(required=False, default=True,
                                                  label=_("Show timeseries data for point"))
    unit = blocks.CharBlock(required=False, label=_("Data unit"))
    timeseries_chart_type = blocks.ChoiceBlock(choices=TIMESERIES_CHART_TYPES, default="bars", label=_("Chart Type"))
    timeseries_chart_color = NativeColorBlock(required=True, default="#367DA4", label=_("Chart Line/Bar Color"))


class FileLayerAreaAnalysisBlock(blocks.StructBlock):
    INSTANCE_VALUE_TYPE_CHOICES = (
        ("mean", _("Mean of pixel values")),
        ("sum", _("Sum of pixel values")),
        ("minmax", _("Minimum, Maximum pixel values")),
        ("minmeanmax", _("Minimum, Mean, Maximum pixel values"))
    )

    TIMESERIES_AGGREGATION_METHODS = (
        ("mean", _("By Mean")),
        ("sum", _("By Sum"))
    )

    instance_data_enabled = blocks.BooleanBlock(required=False, default=True, label=_("Show data for area"))
    instance_value_type = blocks.ChoiceBlock(choices=INSTANCE_VALUE_TYPE_CHOICES, default="mean",
                                             label=_("Area value type"),
                                             help_text=_("The value type that should be displayed"))
    unit = blocks.CharBlock(required=False, label=_("Data unit"))
    timeseries_data_enabled = blocks.BooleanBlock(required=False, default=True,
                                                  label=_("Show timeseries data for area"))
    timeseries_aggregation_method = blocks.ChoiceBlock(choices=TIMESERIES_AGGREGATION_METHODS, default="mean",
                                                       label=_("Area timeseries data aggregation Method"),
                                                       help_text=_("How should the region data be aggregated ?"))

    timeseries_chart_type = blocks.ChoiceBlock(choices=TIMESERIES_CHART_TYPES, default="bars", label=_("Chart Type"))
    timeseries_chart_color = NativeColorBlock(required=True, default="#367DA4", label=_("circle stroke color"))


class LayerMoreInfoStructValue(StructValue):
    @cached_property
    def as_dict(self):
        info = {
            "linkText": self.get("link_text"),
            "linkUrl": self.get("link_url"),
            "text": self.get("text"),
            "isButton": self.get("is_button"),
            "showArrow": self.get("show_arrow"),
        }

        return info


class LayerMoreInfoBlock(blocks.StructBlock):
    link_text = blocks.CharBlock(required=True, label=_("Link text"))
    link_url = blocks.URLBlock(required=True, label=_("Link Url"))
    text = blocks.TextBlock(required=False, label=_("Short description text"))
    is_button = blocks.BooleanBlock(required=False, default=True, label=_("Format link as action button"))
    show_arrow = blocks.BooleanBlock(required=False, default=True, label=_("Show arrow in button"))

    class Meta:
        value_class = LayerMoreInfoStructValue
