from django.forms.widgets import Input


class RasterStyleWidget(Input):
    input_type = "hidden"
    template_name = "geomanager/widgets/raster_style_widget.html"

    class Media:
        js = ('js/vendor/d3-format.min.js', 'js/colorbrewer.js', 'js/widgets/raster_style_widget.js',)
