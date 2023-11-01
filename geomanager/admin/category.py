from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail_adminsortable.admin import SortableAdminMixin
from wagtail_modeladmin.helpers import AdminURLHelper, ButtonHelper
from wagtail_modeladmin.views import CreateView, EditView

from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide
from geomanager.models import Category


class CategoryCreateView(CreateView):
    def get_context_data(self, **kwargs):
        context_data = super(CategoryCreateView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": "#", "label": _("New") + f" {Category._meta.verbose_name}"},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class CategoryEditView(EditView):
    def get_context_data(self, **kwargs):
        context_data = super(CategoryEditView, self).get_context_data(**kwargs)

        category_admin_helper = AdminURLHelper(Category)
        category_index_url = category_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": category_index_url, "label": Category._meta.verbose_name_plural},
            {"url": "#", "label": self.instance.title},
        ]

        context_data.update({
            "navigation_items": navigation_items,
        })

        return context_data


class CategoryButtonHelper(ButtonHelper):
    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        buttons = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)

        create_dataset_button = {
            "url": obj.dataset_create_url(),
            "label": _("Add Dataset"),
            "classname": cn,
            "title": _("Add Dataset") % {"object": self.verbose_name},
        }

        buttons.append(create_dataset_button)

        return buttons


class CategoryModelAdmin(SortableAdminMixin, BaseModelAdmin, ModelAdminCanHide):
    model = Category
    menu_label = _("Datasets")
    exclude_from_explorer = True
    button_helper_class = CategoryButtonHelper
    menu_icon = "layer-group"
    list_display_add_buttons = "__str__"

    create_view_class = CategoryCreateView
    edit_view_class = CategoryEditView

    def __init__(self, parent=None):
        super().__init__(parent)
        self.list_display = ["category_icon"] + (list(self.list_display) or []) + ["view_datasets", "create_dataset",
                                                                                   "mapviewer_map_url"]
        self.category_icon.__func__.short_description = _('Icon')
        self.create_dataset.__func__.short_description = _('Add Dataset')
        self.view_datasets.__func__.short_description = _('View Datasets')
        self.mapviewer_map_url.__func__.short_description = _("View on MapViewer")

    def category_icon(self, obj):
        icon = obj.icon
        if not obj.icon:
            icon = "layer-group"

        icon_html = f"""
           <span class="icon-wrapper">
                <svg class="icon icon-{icon} icon" aria-hidden="true" style="height:40px;width:40px">
                    <use href="#icon-{icon}"></use>
                </svg>
            </span>
        """
        return mark_safe(icon_html)

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

    def create_dataset(self, obj):
        label = _("Add Dataset")
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

        datasets_count = obj.datasets.count()

        button_html = f"""
            <a href="{obj.datasets_list_url()}" class="button button-small button--icon bicolor button-secondary">
                <span class="icon-wrapper">
                    <svg class="icon icon-database icon" aria-hidden="true">
                        <use href="#icon-database"></use>
                    </svg>
                </span>
                {label} ({datasets_count})
            </a>
        """
        return mark_safe(button_html)
