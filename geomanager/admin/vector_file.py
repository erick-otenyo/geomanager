from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.helpers import AdminURLHelper
from wagtail_modeladmin.views import CreateView, EditView, IndexView

from geomanager.admin.base import ModelAdminCanHide, BaseModelAdmin, LayerIndexView, LayerFileDeleteView
from geomanager.models import Dataset, VectorFileLayer, PgVectorTable, Category
from geomanager.views import (
    upload_vector_file,
    publish_vector,
    delete_vector_upload,
    preview_vector_layers
)


class VectorFileLayerCreateView(CreateView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="vector_file")

        dataset_id = self.request.GET.get("dataset_id")
        if dataset_id:
            initial = {**form.initial}
            initial.update({"dataset": dataset_id})
            form.initial = initial
        return form

    def get_context_data(self, **kwargs):
        context_data = super(VectorFileLayerCreateView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": "#", "label": _("New") + f" {VectorFileLayer._meta.verbose_name}"},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class VectorFileLayerEditView(EditView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="vector_file")
        return form

    def get_context_data(self, **kwargs):
        context_data = super(VectorFileLayerEditView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        layer_admin_helper = AdminURLHelper(VectorFileLayer)
        layer_index_url = layer_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": layer_index_url, "label": VectorFileLayer._meta.verbose_name_plural},
            {"url": "#", "label": self.instance.title},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class VectorFileLayerModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = VectorFileLayer
    hidden = True
    exclude_from_explorer = True
    menu_label = _("Vector Layers")
    index_view_class = LayerIndexView
    create_view_class = VectorFileLayerCreateView
    edit_view_class = VectorFileLayerEditView
    list_display = ("title",)
    list_filter = ("dataset",)
    index_template_name = "geomanager/modeladmin/index_without_custom_create.html"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['dataset_link', "uploaded_files", "upload_files",
                                                               'preview_layer', 'mapviewer_map_url']
        self.dataset_link.__func__.short_description = _('Dataset')
        self.uploaded_files.__func__.short_description = _("View Uploaded Files")
        self.upload_files.__func__.short_description = _('Upload Vector Files')
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

    def upload_files(self, obj):
        disabled = "" if not obj.has_data_table else "disabled"

        label = _("Upload Files")
        button_html = f"""
            <a href="{obj.upload_url}" class="button button-small bicolor button--icon" {disabled}>
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-upload"></use>
                    </svg>
                </span>
                {label}
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

    def uploaded_files(self, obj):
        label = _("Uploaded Files")
        button_html = f"""
            <a href="{obj.get_uploads_list_url()}" class="button button-small button--icon bicolor button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-list-ol icon" aria-hidden="true">
                        <use href="#icon-list-ol"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)


class VectorFileIndexView(IndexView):
    def get_context_data(self, **kwargs):
        context_data = super(VectorFileIndexView, self).get_context_data(**kwargs)

        model_verbose_name = self.model._meta.verbose_name_plural

        category_admin_helper = AdminURLHelper(Category)
        categories_url = category_admin_helper.get_action_url("index")

        dataset_admin_helper = AdminURLHelper(Dataset)
        datasets_url = dataset_admin_helper.get_action_url("index")

        layer_admin_helper = AdminURLHelper(VectorFileLayer)
        layers_url = layer_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": categories_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_url, "label": Dataset._meta.verbose_name_plural},
            {"url": layers_url, "label": VectorFileLayer._meta.verbose_name_plural},
            {"url": "#", "label": model_verbose_name},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class VectorTableModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = PgVectorTable
    index_view_class = VectorFileIndexView
    hidden = True
    list_display = ("__str__", "table_name",)
    list_filter = ("layer",)
    index_template_name = "geomanager/modeladmin/index_without_custom_create.html"
    inspect_view_enabled = True
    delete_view_class = LayerFileDeleteView


urls = [
    path('upload-vector/', upload_vector_file, name='geomanager_upload_vector'),
    path('upload-vector/<uuid:dataset_id>/', upload_vector_file, name='geomanager_dataset_upload_vector'),
    path('upload-vector/<uuid:dataset_id>/<uuid:layer_id>/', upload_vector_file,
         name='geomanager_dataset_layer_upload_vector'),
    path('publish-vector/<int:upload_id>/', publish_vector, name='geomanager_publish_vector'),
    path('delete-vector-upload/<int:upload_id>/', delete_vector_upload, name='geomanager_delete_vector_upload'),
    path('preview-vector-layers/<uuid:dataset_id>/', preview_vector_layers, name='geomanager_preview_vector_dataset'),
    path('preview-vector-layers/<uuid:dataset_id>/<uuid:layer_id>/', preview_vector_layers,
         name='geomanager_preview_vector_layer'),
]
