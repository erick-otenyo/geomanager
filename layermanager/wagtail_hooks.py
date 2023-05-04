import os

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.template.loaders.app_directories import get_app_template_dirs
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdminGroup, ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.views import CreateView, EditView
from django.utils.translation import gettext_lazy as _
from wagtail_adminsortable.admin import SortableAdminMixin

from layermanager.helpers import (DatasetButtonHelper, CategoryButtonHelper, FileLayerButtonHelper)
from .icons import OCHA_ICONS
from .models import (
    Category,
    Dataset,
    Metadata,
    FileImageLayer,
    MBTSource
)
from .models.core import SubCategory
from .models.raster import RasterStyle, WmsLayer
from .models.vector import VectorLayer
from .views import (
    upload_raster_file,
    publish_raster,
    delete_raster_upload,
    preview_raster_layers,
    upload_vector_file,
    publish_vector,
    delete_vector_upload,
    preview_vector_layers,
    preview_wms_layers, load_boundary
)


@hooks.register('register_admin_urls')
def urlconf_layermanager():
    return [
        path('upload-rasters/', upload_raster_file, name='layermanager_upload_rasters'),
        path('upload-rasters/<uuid:dataset_id>/', upload_raster_file, name='layermanager_dataset_upload_raster'),
        path('upload-rasters/<uuid:dataset_id>/<uuid:layer_id>/', upload_raster_file,
             name='layermanager_dataset_layer_upload_raster'),

        path('publish-rasters/<int:upload_id>/', publish_raster, name='layermanager_publish_raster'),
        path('delete-raster-upload/<int:upload_id>/', delete_raster_upload, name='layermanager_delete_raster_upload'),

        path('preview-raster-layers/<uuid:dataset_id>/', preview_raster_layers,
             name='layermanager_preview_raster_dataset'),
        path('preview-raster-layers/<uuid:dataset_id>/<uuid:layer_id>/', preview_raster_layers,
             name='layermanager_preview_raster_layer'),

        path('load-boundary/', load_boundary, name='layermanager_load_boundary'),

        path('upload-vector/', upload_vector_file, name='layermanager_upload_vector'),
        path('upload-vector/<uuid:dataset_id>/', upload_vector_file, name='layermanager_dataset_upload_vector'),
        path('upload-vector/<uuid:dataset_id>/<uuid:layer_id>/', upload_vector_file,
             name='layermanager_dataset_layer_upload_vector'),

        path('publish-vector/<int:upload_id>/', publish_vector, name='layermanager_publish_vector'),
        path('delete-vector-upload/<int:upload_id>/', delete_vector_upload, name='layermanager_delete_vector_upload'),

        path('preview-vector-layers/<uuid:dataset_id>/', preview_vector_layers,
             name='layermanager_preview_vector_dataset'),
        path('preview-vector-layers/<uuid:dataset_id>/<uuid:layer_id>/', preview_vector_layers,
             name='layermanager_preview_vector_layer'),

        path('preview-wms-layers/<uuid:dataset_id>/', preview_wms_layers,
             name='layermanager_preview_wms_dataset'),
        path('preview-wms-layers/<uuid:dataset_id>/<uuid:layer_id>/', preview_wms_layers,
             name='layermanager_preview_wms_layer'),
    ]


class ModelAdminCanHide(ModelAdmin):
    hidden = False


class CategoryModelAdmin(SortableAdminMixin, ModelAdminCanHide):
    model = Category
    menu_label = _("Data Categories")
    exclude_from_explorer = True
    button_helper_class = CategoryButtonHelper

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ["create_dataset", 'view_datasets', ]
        self.create_dataset.__func__.short_description = _('Create Dataset')
        self.view_datasets.__func__.short_description = _('View Datasets')

    def create_dataset(self, obj):
        label = _("Create Dataset")
        button_html = f"""
            <a href="{obj.dataset_create_url()}" class="button button-small button--icon bicolor">
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-plus"></use>
                    </svg>
                </span>
              {label}
            </a>
        """
        return mark_safe(button_html)

    def view_datasets(self, obj):
        label = _("View Datasets")
        button_html = f"""
            <a href="{obj.datasets_list_url()}" class="button button-small button--icon bicolor button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-list-ul icon" aria-hidden="true">
                        <use href="#icon-list-ul"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)


class DatasetCreateView(CreateView):
    def get_form(self):
        form = super().get_form()
        category_id = self.request.GET.get("category_id")
        if category_id:
            form.fields["sub_category"].queryset = SubCategory.objects.filter(category=category_id)
            initial = {**form.initial}
            initial.update({"category": category_id})
            form.initial = initial
        return form


class DatasetModelAdmin(ModelAdminCanHide):
    model = Dataset
    exclude_from_explorer = True
    button_helper_class = DatasetButtonHelper
    list_display = ("__str__", "layer_type",)

    list_filter = ("category", "id",)
    create_view_class = DatasetCreateView

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['category_link', 'view_layers', 'upload_files',
                                                               'preview_dataset', ]
        self.category_link.__func__.short_description = _('Category')
        self.view_layers.__func__.short_description = _('View Layers')
        self.upload_files.__func__.short_description = _('Upload Files')
        self.preview_dataset.__func__.short_description = _('Preview on Map')

    def category_link(self, obj):
        label = _("Edit Category")
        button_html = f"""
            <a href="{obj.category_url}">
                {label}
            </a>
        """
        return mark_safe(button_html)

    def view_layers(self, obj):
        label = _("Layers")
        button_html = f"""
            <a href="{obj.layers_list_url()}" class="button button-small button--icon bicolor button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-list-ol icon" aria-hidden="true">
                        <use href="#icon-list-ol"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)

    def preview_dataset(self, obj):
        if not obj.preview_url:
            return None
        disabled = "" if obj.can_preview() else "disabled"
        label = _("Preview Dataset")
        button_html = f"""
            <a href="{obj.preview_url}" class="button button-small button--icon button-secondary {disabled}">
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-view"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)

    def upload_files(self, obj):
        if not obj.upload_url:
            return None
        disabled = "" if obj.has_layers() else "disabled"
        label = _("Upload Files")
        button_html = f"""
            <a href="{obj.upload_url}" class="button button-small bicolor button--icon {disabled}">
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-upload"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)


class FileImageLayerCreateView(CreateView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="file")

        dataset_id = self.request.GET.get("dataset_id")
        if dataset_id:
            initial = {**form.initial}
            initial.update({"dataset": dataset_id})
            form.initial = initial
        return form


class FileImageLayerEditView(EditView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="file")
        return form


class FileImageLayerModelAdmin(ModelAdminCanHide):
    model = FileImageLayer
    hidden = True
    exclude_from_explorer = True
    menu_label = _("File Layers")
    button_helper_class = FileLayerButtonHelper
    create_view_class = FileImageLayerCreateView
    edit_view_class = FileImageLayerEditView
    list_display = ("title",)
    list_filter = ("dataset",)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['dataset_link', "upload_files", 'preview_layer']
        self.dataset_link.__func__.short_description = _('Dataset')
        self.upload_files.__func__.short_description = _('Upload Raster Files')
        self.preview_layer.__func__.short_description = _('Preview on Map')

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


class MetadataModelAdmin(ModelAdminCanHide):
    model = Metadata
    exclude_from_explorer = True


class ModelAdminGroupWithHiddenItems(ModelAdminGroup):
    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for model_admin in self.modeladmin_instances:
            if not model_admin.hidden:
                menu_items.append(model_admin.get_menu_item(order=item_order))
                item_order += 1
        return menu_items


class RasterStyleCreateView(CreateView):
    def get_form(self):
        form = super().get_form()

        layer_id = self.request.GET.get("layer_id")

        # add hidden layer_id field to form. We will use it later to update the layer style
        if layer_id:
            try:
                layer = FileImageLayer.objects.get(pk=layer_id)
                form.fields["layer_id"] = forms.CharField(required=False, widget=forms.HiddenInput())
                form.initial.update({"layer_id": layer.pk})
            except ObjectDoesNotExist:
                pass

        return form

    def form_valid(self, form):
        response = super().form_valid(form)

        # check if we have layer_id in data
        layer_id = form.data.get("layer_id")

        if layer_id:
            try:
                # assign this layer the just created style
                layer = FileImageLayer.objects.get(pk=layer_id)
                layer.style = self.instance
                layer.save()
            except ObjectDoesNotExist:
                pass

        return response


class RasterStyleModelAdmin(ModelAdminCanHide):
    model = RasterStyle
    exclude_from_explorer = True
    create_view_class = RasterStyleCreateView
    list_display = ("__str__", "min", "max", "steps")
    form_view_extra_js = ["js/raster_style_extra.js"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['preview']
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


class WmsLayerModelAdmin(ModelAdminCanHide):
    model = WmsLayer
    exclude_from_explorer = True
    create_view_class = WmsLayerCreateView
    hidden = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['dataset_link', 'preview_layer']
        self.dataset_link.__func__.short_description = _('Dataset')
        self.preview_layer.__func__.short_description = _('Preview on Map')

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


class VectorLayerCreateView(CreateView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="vector")

        dataset_id = self.request.GET.get("dataset_id")
        if dataset_id:
            initial = {**form.initial}
            initial.update({"dataset": dataset_id})
            form.initial = initial
        return form


class VectorLayerEditView(EditView):
    def get_form(self):
        form = super().get_form()
        form.fields["dataset"].queryset = Dataset.objects.filter(layer_type="vector")
        return form


class VectorLayerModelAdmin(ModelAdminCanHide):
    model = VectorLayer
    hidden = True
    exclude_from_explorer = True
    menu_label = _("Vector Layers")
    create_view_class = VectorLayerCreateView
    edit_view_class = VectorLayerEditView
    list_display = ("title",)
    list_filter = ("dataset",)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['dataset_link', "upload_files", 'preview_layer']
        self.dataset_link.__func__.short_description = _('Dataset')
        self.upload_files.__func__.short_description = _('Upload Vector Files')
        self.preview_layer.__func__.short_description = _('Preview on Map')

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


class MBTSourceModelAdmin(ModelAdminCanHide):
    model = MBTSource
    menu_label = _("Basemap Styles")


class LayerManagerAdminGroup(ModelAdminGroupWithHiddenItems):
    menu_label = _('Layer Manager')
    menu_icon = 'folder-inverse'
    menu_order = 700
    items = (
        CategoryModelAdmin, DatasetModelAdmin, MetadataModelAdmin, FileImageLayerModelAdmin,
        RasterStyleModelAdmin, VectorLayerModelAdmin, WmsLayerModelAdmin, MBTSourceModelAdmin)

    def get_submenu_items(self):
        menu_items = super().get_submenu_items()

        boundary_loader = MenuItem(label=_("Boundary Loader"), url=reverse("layermanager_load_boundary"),
                                   icon_name="upload")
        menu_items.append(boundary_loader)

        return menu_items


modeladmin_register(LayerManagerAdminGroup)


@hooks.register("register_icons")
def register_icons(icons):
    for icon in OCHA_ICONS:
        icons.append("layermanager/ocha_icons/{}".format(icon))
    return icons
