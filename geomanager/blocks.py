from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail_color_panel.blocks import NativeColorBlock


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


# A filled polygon with an optional stroked border
class FillVectorLayerBlock(blocks.StructBlock):
    paint = blocks.StructBlock([
        ('fill_antialias', blocks.BooleanBlock(required=False, default=True, label=_("fill antialias"))),
        ('fill_color', NativeColorBlock(default="#000000", label=_("fill color"))),
        ('fill_opacity', blocks.IntegerBlock(default=1, validators=[MinValueValidator(0), MaxValueValidator(1)],
                                             label=_("fill opacity"))),
        ('fill_outline_color', NativeColorBlock(default="#000000", label=_("fill outline color"))),
    ], label="Paint Properties")

    filter = blocks.CharBlock(required=False, label=_("filter"))
    maxzoom = blocks.IntegerBlock(required=False, label=_("maxzoom"))
    minzoom = blocks.IntegerBlock(required=False, label=_("minzoom"))


# A stroked line
class LineVectorLayerBlock(blocks.StructBlock):
    paint = blocks.StructBlock([
        ('line_color', NativeColorBlock(default="#000000", label=_("line color"))),
        ('line_opacity', blocks.IntegerBlock(validators=[MinValueValidator(0), MaxValueValidator(1)], default=1,
                                             label=_("line opacity"))),
        ('line_width', blocks.IntegerBlock(validators=[MinValueValidator(0)], default=1, label=_("line_width"))),
    ], label="Paint Properties")

    filter = blocks.CharBlock(required=False, label=_("filter"))
    maxzoom = blocks.IntegerBlock(required=False, label=_("maxzoom"))
    minzoom = blocks.IntegerBlock(required=False, label=_("minzoom"))


# An icon
class SymbolVectorLayerBlock(blocks.StructBlock):
    pass


# Text label
class TextVectorLayerBlock(blocks.StructBlock):
    pass


# A filled circle
class CircleVectorLayerBlock(blocks.StructBlock):
    paint = blocks.StructBlock([
        ('circle_color', NativeColorBlock(default="#000000", label=_("circle color"))),
        ('circle_opacity', blocks.IntegerBlock(validators=[MinValueValidator(0), MaxValueValidator(1)], default=1,
                                               label=_("circle opacity"))),
        ('circle_radius', blocks.IntegerBlock(validators=[MinValueValidator(0)], default=5, label=_("circle radius"))),
        ('circle_stroke_color', NativeColorBlock(default="#000000", label=_("circle stroke color"))),
        ('circle_opacity', blocks.IntegerBlock(validators=[MinValueValidator(0), MaxValueValidator(1)], default=1,
                                               label=_("circle opacity"))),
        ('circle_stroke_width', blocks.IntegerBlock(validators=[MinValueValidator(0)], default=0,
                                                    label=_("circle_stroke_width"))),

    ], label="Paint Properties")

    filter = blocks.CharBlock(required=False, label=_("filter"))
    maxzoom = blocks.IntegerBlock(required=False, label=_("maxzoom"))
    minzoom = blocks.IntegerBlock(required=False, label=_("minzoom"))
