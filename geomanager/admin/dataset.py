from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.helpers import AdminURLHelper, ButtonHelper
from wagtail_modeladmin.views import IndexView, CreateView, EditView

from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide
from geomanager.models import Category, Dataset, SubCategory


class DatasetIndexView(IndexView):
    def get_context_data(self, **kwargs):
        context_data = super(DatasetIndexView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": "#", "label": Dataset._meta.verbose_name_plural},
        ]

        context_data.update({
            "custom_create_url": {
                "label": _("Create from categories"),
                "url": category_index_url
            },
            "navigation_items": navigation_items,
        })

        return context_data


class DatasetCreateView(CreateView):
    def get_form(self):
        form = super().get_form()
        category_id = self.request.GET.get("category_id")
        if category_id:
            # form.fields["category"].widget.attrs.update({"disabled": "true"})
            form.fields["sub_category"].queryset = SubCategory.objects.filter(category=category_id)
            initial = {**form.initial}
            initial.update({"category": category_id})
            form.initial = initial
        return form

    def get_context_data(self, **kwargs):
        context_data = super(DatasetCreateView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": "#", "label": _("New") + f" {Dataset._meta.verbose_name}"},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class DatasetEditView(EditView):
    def get_context_data(self, **kwargs):
        context_data = super(DatasetEditView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        datasets_admin_helper = AdminURLHelper(Dataset)
        datasets_index_url = datasets_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": datasets_index_url, "label": Dataset._meta.verbose_name_plural},
            {"url": "#", "label": self.instance.title},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class DatasetButtonHelper(ButtonHelper):
    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        buttons = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)

        layer_create_url = obj.create_layer_url()

        if layer_create_url:
            create_layer_button = {
                "url": obj.create_layer_url(),
                "label": _("Add Layer"),
                "classname": cn,
                "title": _("Add %(object)s Layer") % {"object": self.verbose_name},
            }
            buttons.append(create_layer_button)

        return buttons


class DatasetModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    hidden = True
    model = Dataset
    exclude_from_explorer = True
    button_helper_class = DatasetButtonHelper
    list_display = ("__str__", "layer_type",)
    list_filter = ("category",)
    index_template_name = "geomanager/modeladmin/index_without_custom_create.html"
    menu_icon = "database"

    index_view_class = DatasetIndexView
    create_view_class = DatasetCreateView
    edit_view_class = DatasetEditView

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = (list(self.list_display) or []) + ['view_layers', 'mapviewer_map_url']

        self.view_layers.__func__.short_description = _('Layers')
        self.mapviewer_map_url.__func__.short_description = _("View on MapViewer")

    def mapviewer_map_url(self, obj):
        label = _("MapViewer")

        if not obj.has_layers():
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

    def category_link(self, obj):
        label = _("Edit Category")
        button_html = f"""
            <a href="{obj.category_url}">
                {label}
            </a>
        """
        return mark_safe(button_html)

    def add_layer(self, obj):
        label = _("Add Layer")
        button_html = f"""
            <a href="{obj.create_layer_url()}" class="button button-small bicolor button--icon ">
                <span class="icon-wrapper">
                    <svg class="icon icon-plus icon" aria-hidden="true">
                        <use href="#icon-plus"></use>
                    </svg>
                </span>
                {label}
            </a>
        """

        return mark_safe(button_html)

    def view_layers(self, obj):
        label = _("View Layers")

        if not obj.has_layers():
            return self.add_layer(obj)

        button_html = f"""
            <a href="{obj.layers_list_url()}" class="button button-small button--icon bicolor button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-layer-group icon" aria-hidden="true">
                        <use href="#icon-layer-group"></use>
                    </svg>
                </span>
                {label}
            </a>
        """
        return mark_safe(button_html)

    def preview_dataset(self, obj):
        if not obj.preview_url:
            return None

        if obj.layer_type == "vector_file":
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
