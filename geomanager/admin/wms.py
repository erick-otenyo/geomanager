from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.helpers import AdminURLHelper
from wagtail_modeladmin.views import CreateView, EditView

from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide, LayerIndexView
from geomanager.models import Dataset, WmsLayer, Category
from geomanager.views import preview_wms_layers


class WmsLayerCreateView(CreateView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="wms")

        dataset_id = self.request.GET.get("dataset_id")
        if dataset_id:
            initial = {**form.initial}
            initial.update({"dataset": dataset_id})
            form.initial = initial
        return form

    def get_context_data(self, **kwargs):
        context_data = super(WmsLayerCreateView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": "#", "label": _("New") + f" {WmsLayer._meta.verbose_name}"},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class WMSLayerEditView(EditView):
    def get_context_data(self, **kwargs):
        context_data = super(WMSLayerEditView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        layer_admin_helper = AdminURLHelper(WmsLayer)
        layer_index_url = layer_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": layer_index_url, "label": WmsLayer._meta.verbose_name_plural},
            {"url": "#", "label": self.instance.title},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class WmsLayerModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = WmsLayer

    exclude_from_explorer = True
    hidden = True

    index_template_name = "geomanager/modeladmin/index_without_custom_create.html"

    index_view_class = LayerIndexView
    create_view_class = WmsLayerCreateView
    edit_view_class = WMSLayerEditView

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['dataset_link', 'preview_layer', "mapviewer_map_url"]
        self.dataset_link.__func__.short_description = _('Dataset')
        self.preview_layer.__func__.short_description = _('Preview on Map')
        self.mapviewer_map_url.__func__.short_description = _("View on MapViewer")

    def mapviewer_map_url(self, obj):
        label = _("MapViewer")
        button_html = f"""
            <a href="{obj.mapviewer_map_url}" target="_blank" rel="noopener noreferrer" class="button button-small button--icon button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-map icon" aria-hidden="true">
                        <use href="#icon-map"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)

    def dataset_link(self, obj):
        button_html = f"""
            <a href="{obj.dataset.dataset_url()}">
                {obj.dataset.title}
            </a>
        """
        return mark_safe(button_html)

    def preview_layer(self, obj):
        label = _("Preview Layer")
        button_html = f"""
            <a href="{obj.preview_url}" class="button button-small button--icon button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-view"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)


urls = [
    path('preview-wms-layers/<uuid:dataset_id>/', preview_wms_layers, name='geomanager_preview_wms_dataset'),
    path('preview-wms-layers/<uuid:dataset_id>/<uuid:layer_id>/', preview_wms_layers,
         name='geomanager_preview_wms_layer'),
]
