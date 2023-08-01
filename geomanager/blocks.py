from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail_color_panel.blocks import NativeColorBlock
from wagtailiconchooser.blocks import IconChooserBlock


class NavigationItemsBlock(blocks.StructBlock):
    label = blocks.CharBlock(label=_("Label"))
    page = blocks.PageChooserBlock(required=False, label=_("Page"), help_text=_("Internal page to navigate"))
    external_link = blocks.URLBlock(required=False, label=_("External Link"),
                                    help_text=_("External link to navigate to. Used if internal page not provided"))


class WmsRequestParamSelectableBlock(blocks.StructBlock):
    SELECTOR_TYPE_CHOICES = (
        ("radio", "Radio"),
        ("dropdown", "Dropdown"),
    )
    name = blocks.CharBlock(label=_("name"))
    label = blocks.CharBlock(required=False, label=_("label"))
    type = blocks.ChoiceBlock(choices=SELECTOR_TYPE_CHOICES, default="radio", label=_("Selector Type"))
    options = blocks.ListBlock(blocks.StructBlock([
        ('label', blocks.CharBlock(label=_("label"))),
        ('value', blocks.CharBlock(label=_("value"))),
        ('default',
         blocks.BooleanBlock(required=False, label=_("default"), help_text=_("Check to make default option")))]
    ), min_num=1, label=_("Options"))


class InlineLegendBlock(blocks.StructBlock):
    LEGEND_TYPES = (
        ("basic", "Basic"),
        ("gradient", "Gradient"),
        ("choropleth", "Choropleth"),
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
        ('fill_color', NativeColorBlock(required=False, default="#000000", label=_("fill color"))),
        ('fill_opacity', blocks.FloatBlock(required=False, default=1.0,
                                           validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           label=_("fill opacity"))),
        ('fill_outline_color', NativeColorBlock(required=False, default="#000000", label=_("fill outline color"))),
        ('fill_antialias', blocks.BooleanBlock(required=False, default=True, label=_("fill antialias"))),
    ], label="Paint Properties")

    filter = blocks.CharBlock(required=False, label=_("filter"))
    maxzoom = blocks.IntegerBlock(required=False, label=_("maxzoom"))
    minzoom = blocks.IntegerBlock(required=False, label=_("minzoom"))


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
        ('line_color', NativeColorBlock(required=False, default="#000000", label=_("Line color"))),
        ('line_dasharray', blocks.CharBlock(required=False, label=_("Line dasharray"))),
        ('line_gap_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                             label=_("Line gap width"))),
        ('line_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           default=1.0, label=_("line opacity"))),
        ('line_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=1.0,
                                         label=_("Line width"))),
        ('line_offset', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0,
                                          label=_("Line offset"))),

        # Not implemented here
        # line-gradient - reason => requires source to be geojson, but our source is vector tiles
        # line-pattern
        # line-translate
        # line-translate-anchor
        # line-trim-offset

    ], label="Paint Properties")

    layout = blocks.StructBlock([
        ('line_cap', blocks.ChoiceBlock(required=False, choices=LINE_CAP_CHOICES, default="butt", label=_("Line cap"))),
        ('line_join', blocks.ChoiceBlock(required=False, choices=LINE_JOIN_CHOICES, default="miter",
                                         label=_("Line join"))),
        ('line_miter_limit', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=2.0,
                                               label=_("line miter limit"))),
        ('line_round_limit', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=1.05,
                                               label=_("line round limit"))),

        # Note implemented here
        # line-sort-key

    ], label="Layout Properties")

    filter = blocks.CharBlock(required=False, label=_("filter"))
    maxzoom = blocks.IntegerBlock(required=False, label=_("maxzoom"))
    minzoom = blocks.IntegerBlock(required=False, label=_("minzoom"))


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
        ('icon_allow_overlap', blocks.BooleanBlock(required=False, default=False, label=_("Icon allow overlap"))),
        ('icon_anchor', blocks.ChoiceBlock(required=False, choices=SYMBOL_ANCHOR_CHOICES, default="center",
                                           label=_("Icon anchor"))),
        ('icon_ignore_placement', blocks.BooleanBlock(required=False, default=False, label=_("Icon ignore placement"))),
        ('icon_keep_upright', blocks.BooleanBlock(required=False, default=False, label=_("Icon keep upright"))),
        ('icon_offset', blocks.CharBlock(required=False, label=_("Icon offset"))),
        ('icon_optional', blocks.BooleanBlock(required=False, default=False, label=_("Icon optional"))),
        ('icon_padding', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=2.0,
                                           label=_("Icon padding"))),
        ('icon_pitch_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto",
                                                    label=_("Icon pitch alignment"))),
        ('icon_rotate', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(360)],
                                            default=0, label=_("icon rotate"))),
        ('icon_rotation_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto",
                                                       label=_("Icon rotation alignment"))),
        ('icon_size',
         blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)], default=1,
                           label=_("icon size"))),
        ('icon_text_fit', blocks.ChoiceBlock(required=False, choices=ICON_TEXT_FIT_CHOICES, default="none",
                                             label=_("Icon text fit"))),

        # Not implemented yet
        # icon-text-fit-padding
        # symbol-avoid-edges

    ], label="Layout Properties")

    paint = blocks.StructBlock([
        ('icon_color', NativeColorBlock(required=False, default="#000000", label=_("Icon color"))),
        ('icon_halo_blur', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                             label=_("Icon halo blur"))),
        ('icon_halo_color', NativeColorBlock(required=False, default="#000000", label=_("Icon halo color"))),
        ('icon_halo_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                              label=_("icon halo width"))),
        ('icon_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           default=1.0, label=_("icon opacity"))),

        # Not implemented yet
        # icon-translate
        # icon-translate-anchor

    ], label="Paint Properties")


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
        ('text_color', NativeColorBlock(required=False, default="#000000", label=_("Text color"))),
        ('text_halo_blur', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                             label=_("Text halo blur"))),
        ('text_halo_color', NativeColorBlock(required=False, default="#000000", label=_("Text halo color"))),
        ('text_halo_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                              label=_("text halo width"))),
        ('text_translate', blocks.CharBlock(required=False, label=_("Text translate"))),
        ('text_translate_anchor', blocks.ChoiceBlock(required=False, choices=TEXT_TRANSLATE_ANCHOR_CHOICES,
                                                     default="map", label=_("Text translate anchor"))),
    ], label="Paint Properties")

    layout = blocks.StructBlock([
        ('symbol_placement', blocks.ChoiceBlock(required=False, choices=SYMBOL_PLACEMENT_CHOICES, default="point",
                                                label=_("Text Placement"))),
        ('text_allow_overlap', blocks.BooleanBlock(required=False, default=False, label=_("Text allow overlap"))),
        ('text_anchor', blocks.ChoiceBlock(required=False, choices=SYMBOL_ANCHOR_CHOICES, default="center",
                                           label=_("Text anchor"))),

        ('text_field', blocks.CharBlock(label=_("Text field"))),
        ('text_size', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=16,
                                          label=_("Text size"))),
        ('text_transform', blocks.ChoiceBlock(required=False, choices=TEXT_TRANSFORM_CHOICES, default="none",
                                              label=_("Text transform"))),
        ('text_ignore_placement', blocks.BooleanBlock(required=False, default=False, label=_("Text ignore placement"))),
        ('text_justify', blocks.ChoiceBlock(required=False, choices=TEXT_JUSTIFY_CHOICES, default="center",
                                            label=_("Text justify"))),
        ('text_keep_upright', blocks.BooleanBlock(required=False, default=False, label=_("Text keep upright"))),
        ('text_letter_spacing', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                                  label=_("Text letter spacing"))),
        ('text_line_height', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=1.2,
                                               label=_("Text line height"))),
        ('text_max_angle', blocks.IntegerBlock(required=False,
                                               validators=[MinValueValidator(0), MaxValueValidator(360)], default=45,
                                               label=_("Text max angle"))),
        ('text_max_width', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=10,
                                               label=_("Text max width"))),
        ('text_offset', blocks.CharBlock(required=False, label=_("Text offset"))),
        ('text_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                           default=1.0, label=_("text opacity"))),
        ('text_padding', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=2,
                                             label=_("Text  padding"))),
        ('text_pitch_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto",
                                                    label=_("Text pitch alignment"))),
        ('text_radial_offset', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0)], default=0,
                                                   label=_("Text radial offset"))),
        ('text_rotate', blocks.IntegerBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(360)],
                                            default=0, label=_("Text rotate"))),
        ('text_rotation_alignment', blocks.ChoiceBlock(required=False, choices=SYMBOL_ALIGNMENT_CHOICES, default="auto",
                                                       label=_("Text rotation alignment"))),

        ('text_variable_anchor', blocks.ChoiceBlock(required=False, choices=SYMBOL_ANCHOR_CHOICES,
                                                    label=_("Text variable anchor"))),

        # Not implemented yet
        # symbol-avoid-edges
        # symbol-sort-key
        # symbol-spacing
        # text-font - reason => we should control the fonts used
        # text-optional
        # text-writing-mode

    ], label="Layout Properties")


# A filled circle
class CircleVectorLayerBlock(blocks.StructBlock):
    paint = blocks.StructBlock([
        ('circle_color', NativeColorBlock(required=False, default="#000000", label=_("circle color"))),
        ('circle_opacity', blocks.FloatBlock(required=False, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                             default=1.0, label=_("circle opacity"))),
        ('circle_radius', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=5.0,
                                            label=_("circle radius"))),
        ('circle_stroke_color', NativeColorBlock(required=False, default="#000000", label=_("circle stroke color"))),
        ('circle_stroke_width', blocks.FloatBlock(required=False, validators=[MinValueValidator(0)], default=0.0,
                                                  label=_("circle_stroke_width"))),

    ], label="Paint Properties")

    filter = blocks.CharBlock(required=False, label=_("filter"))
    maxzoom = blocks.IntegerBlock(required=False, label=_("maxzoom"))
    minzoom = blocks.IntegerBlock(required=False, label=_("minzoom"))


TIMESERIES_CHART_TYPES = (
    ("lines", "Line Chart"),
    ("bars", "Bar Chart"),
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
        ("mean", "Mean of pixel values"),
        ("sum", "Sum of pixel values"),
        ("minmax", "Minimum, Maximum pixel values"),
        ("minmeanmax", "Minimum, Mean, Maximum pixel values")
    )

    TIMESERIES_AGGREGATION_METHODS = (
        ("mean", "By Mean"),
        ("sum", "By Sum")
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
