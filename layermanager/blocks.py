from wagtail import blocks
from django.utils.translation import gettext_lazy as _


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
