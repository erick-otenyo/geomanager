from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.helpers import AdminURLHelper, ButtonHelper
from wagtail_modeladmin.views import CreateView, EditView, IndexView

from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide, LayerIndexView, LayerFileDeleteView
from geomanager.models import Dataset, RasterFileLayer, LayerRasterFile, Category
from geomanager.views import (
    upload_raster_file,
    publish_raster,
    delete_raster_upload,
    preview_raster_layers
)


class RasterFileLayerCreateView(CreateView):
    form_view_extra_js = ["geomanager/js/raster-file-conditional.js"]

    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="raster_file")

        dataset_id = self.request.GET.get("dataset_id")
        if dataset_id:
            initial = {**form.initial}
            initial.update({"dataset": dataset_id})
            form.initial = initial
        return form

    def get_context_data(self, **kwargs):
        context_data = super(RasterFileLayerCreateView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": "#", "label": _("New") + f" {RasterFileLayer._meta.verbose_name}"},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class RasterFileLayerEditView(EditView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="raster_file")
        return form

    def get_context_data(self, **kwargs):
        context_data = super(RasterFileLayerEditView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        layer_admin_helper = AdminURLHelper(RasterFileLayer)
        layer_index_url = layer_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": layer_index_url, "label": RasterFileLayer._meta.verbose_name_plural},
            {"url": "#", "label": self.instance.title},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class RasterFileLayerButtonHelper(ButtonHelper):
    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        buttons = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)

        url = obj.get_style_url()

        layer_style_button = {
            "url": url.get("url"),
            "label": _(url.get("action")),
            "classname": cn,
            "title": _(url.get("action")) % {"object": self.verbose_name},
        }

        buttons.append(layer_style_button)

        return buttons


class RasterFileLayerModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = RasterFileLayer
    hidden = True
    exclude_from_explorer = True
    menu_label = _("File Layers")
    button_helper_class = RasterFileLayerButtonHelper
    list_display = ("title",)
    list_filter = ("dataset",)
    index_template_name = "geomanager/modeladmin/index_without_custom_create.html"
    list_display_add_buttons = "title"

    index_view_class = LayerIndexView
    create_view_class = RasterFileLayerCreateView
    edit_view_class = RasterFileLayerEditView

    form_view_extra_js = ["geomanager/js/raster-file-conditional.js"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = ["thumbnail_url"] + (list(self.list_display) or []) + ["dataset_link", "upload_files",
                                                                                   "uploaded_files", "preview_layer",
                                                                                   "mapviewer_map_url"]
        self.thumbnail_url.__func__.short_description = _("Thumbnail")
        self.dataset_link.__func__.short_description = _("Dataset")
        self.uploaded_files.__func__.short_description = _("Uploaded Files")
        self.upload_files.__func__.short_description = _("Upload Raster Files")
        self.preview_layer.__func__.short_description = _("Preview")
        self.mapviewer_map_url.__func__.short_description = _("MapViewer")

    def thumbnail_url(self, obj):
        raster_file = obj.raster_files.first()

        if raster_file:
            latest_upload_time = raster_file.time.strftime("%Y-%m-%d %H:%M:%S")

            return mark_safe(f"""
            <div class="thumbnail">
                <img src="{raster_file.thumbnail_url}" width="100" height="100">
                <div class="thumbnail__caption">
                    <b> Latest Upload: {latest_upload_time}</b> 
                </div>
            </div>
            """)

        return None

    def mapviewer_map_url(self, obj):
        label = _("MapViewer")
        if obj.raster_files_count == 0:
            return None

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
        label = _("Upload Files")
        button_html = f"""
            <a href="{obj.upload_url}" class="button button-small bicolor button--icon">
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-upload"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)

    def uploaded_files(self, obj):
        label = _("View Uploaded Files")

        if obj.raster_files_count == 0:
            return None

        button_html = f"""
            <a href="{obj.get_uploads_list_url()}" class="button button-small button--icon bicolor button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-list-ol icon" aria-hidden="true">
                        <use href="#icon-list-ol"></use>
                    </svg>
                </span>
                {label} ({obj.raster_files_count})
            </a>
        """
        return mark_safe(button_html)

    def preview_layer(self, obj):
        label = _("Preview Layer")

        if obj.raster_files_count == 0:
            return None

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


class RasterFileIndexView(IndexView):
    def get_context_data(self, **kwargs):
        context_data = super(RasterFileIndexView, self).get_context_data(**kwargs)

        model_verbose_name = self.model._meta.verbose_name_plural

        category_admin_helper = AdminURLHelper(Category)
        categories_url = category_admin_helper.get_action_url("index")

        dataset_admin_helper = AdminURLHelper(Dataset)
        datasets_url = dataset_admin_helper.get_action_url("index")

        layer_admin_helper = AdminURLHelper(RasterFileLayer)
        layers_url = layer_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": categories_url, "label": _("Categories")},
            {"url": datasets_url, "label": _("Datasets")},
            {"url": layers_url, "label": _("Raster File Layers")},
            {"url": "#", "label": model_verbose_name},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class RasterFileEditView(EditView):
    def get_context_data(self, **kwargs):
        context_data = super(RasterFileEditView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        categories_url = category_admin_helper.get_action_url("index")

        dataset_admin_helper = AdminURLHelper(Dataset)
        datasets_url = dataset_admin_helper.get_action_url("index")

        layer_admin_helper = AdminURLHelper(RasterFileLayer)
        layers_url = layer_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": categories_url, "label": _("Categories")},
            {"url": datasets_url, "label": _("Datasets")},
            {"url": layers_url, "label": _("Raster File Layers")},
            {"url": "#", "label": self.instance}
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class RasterFileModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = LayerRasterFile
    exclude_from_explorer = True
    hidden = True

    list_display = ("thumbnail", "__str__", "layer", "time",)
    list_filter = ("layer",)
    list_display_add_buttons = "__str__"
    index_template_name = "geomanager/modeladmin/index_without_custom_create.html"

    index_view_class = RasterFileIndexView
    edit_view_class = RasterFileEditView
    delete_view_class = LayerFileDeleteView

    def thumbnail(self, obj):
        return mark_safe(f"""
            <a href="{obj.thumbnail_url}" target="_blank">
                <img src="{obj.thumbnail_url}" width="100" height="100" />
            </a>""")


urls = [
    path('upload-rasters/', upload_raster_file, name='geomanager_upload_rasters'),
    path('upload-rasters/<uuid:dataset_id>/', upload_raster_file, name='geomanager_dataset_upload_raster'),
    path('upload-rasters/<uuid:dataset_id>/<uuid:layer_id>/', upload_raster_file,
         name='geomanager_dataset_layer_upload_raster'),

    path('publish-rasters/<int:upload_id>/', publish_raster, name='geomanager_publish_raster'),
    path('delete-raster-upload/<int:upload_id>/', delete_raster_upload, name='geomanager_delete_raster_upload'),

    path('preview-raster-layers/<uuid:dataset_id>/', preview_raster_layers,
         name='geomanager_preview_raster_dataset'),
    path('preview-raster-layers/<uuid:dataset_id>/<uuid:layer_id>/', preview_raster_layers,
         name='geomanager_preview_raster_layer'),
]
