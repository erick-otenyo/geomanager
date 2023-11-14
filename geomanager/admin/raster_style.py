from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.views import CreateView

from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide
from geomanager.models import RasterFileLayer, RasterStyle


class RasterStyleCreateView(CreateView):
    def get_form(self):
        form = super().get_form()

        try:
            # check if we have layer_id in GET
            layer_id = self.request.GET.get("layer_id")

            # add hidden layer_id field to form. We will use it later to update the layer style
            if layer_id:
                layer = RasterFileLayer.objects.get(pk=layer_id)
                form.fields["layer_id"] = forms.CharField(required=False, widget=forms.HiddenInput())
                form.initial.update({"layer_id": layer.pk})
        except Exception:
            pass

        return form

    def form_valid(self, form):
        response = super().form_valid(form)

        try:
            # check if we have layer_id in data
            layer_id = form.data.get("layer_id")

            if layer_id:
                # assign this layer the just created style
                layer = RasterFileLayer.objects.get(pk=layer_id)
                layer.style = self.instance
                layer.save()
        except Exception:
            pass

        return response


class RasterStyleModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = RasterStyle
    exclude_from_explorer = True
    create_view_class = RasterStyleCreateView
    list_display = ("__str__", "min", "max")
    form_view_extra_js = ["geomanager/js/raster_style_extra.js"]
    menu_icon = "palette"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ["preview"]
        self.preview.__func__.short_description = _("Color Preview")

    def preview(self, obj):
        if obj.use_custom_colors:
            return None
        color_list = [f"<li style='background-color:{color};height:20px;flex:1;'><li/>" for color in
                      obj.palette.split(",")]
        html = f"""
            <ul style='display:flex;width:200px;box-shadow: 0 1px 6px rgba(0, 0, 0, 0.12), 0 1px 4px rgba(0, 0, 0, 0.12);'>
                {''.join(color_list)}
            </ul>
        """
        return mark_safe(html)
