from io import BytesIO
from xml.dom import minidom

from cairosvg import svg2png
from django.utils.safestring import mark_safe
from wagtailiconchooser.utils import get_svg_icons


def rasterize_svg_to_png(icon_name, fill_color=None):
    svg_icons = get_svg_icons()

    svg_str = svg_icons.get(icon_name)

    if not svg_str:
        return None

    doc = minidom.parseString(svg_str)
    svg = doc.getElementsByTagName("svg")
    if svg:
        svg = svg[0]

        svg.setAttribute("height", "26")
        svg.setAttribute("width", "26")

        if fill_color:
            svg.setAttribute("fill", fill_color)
            svg_str = mark_safe(svg.toxml())

    svg_bytes = svg_str.encode('utf-8')

    in_buf = BytesIO(svg_bytes)

    # Prepare a buffer for output
    out_buf = BytesIO()

    # Rasterise the SVG to PNG
    svg2png(file_obj=in_buf, write_to=out_buf)
    out_buf.seek(0)

    # Return a Willow PNGImageFile
    return out_buf
