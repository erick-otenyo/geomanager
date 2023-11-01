from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.helpers import AdminURLHelper
from wagtail_modeladmin.options import ModelAdmin
from wagtail_modeladmin.views import IndexView, DeleteView

from geomanager.models import Dataset, Category


class BaseModelAdmin(ModelAdmin):
    index_template_name = "geomanager/modeladmin/index.html"
    create_template_name = "geomanager/modeladmin/create.html"
    edit_template_name = "geomanager/modeladmin/edit.html"


class ModelAdminCanHide(ModelAdmin):
    hidden = False


class LayerIndexView(IndexView):
    def get_context_data(self, **kwargs):
        context_data = super(LayerIndexView, self).get_context_data(**kwargs)

        model_verbose_name = self.model._meta.verbose_name_plural

        dataset_admin_helper = AdminURLHelper(Dataset)
        datasets_url = dataset_admin_helper.get_action_url("index")

        category_admin_helper = AdminURLHelper(Category)
        categories_url = category_admin_helper.get_action_url("index")

        navigation_items = [
            {"url": categories_url, "label": _("Categories")},
            {"url": datasets_url, "label": _("Datasets")},
            {"url": "#", "label": model_verbose_name},
        ]

        context_data.update({
            "custom_create_url": {
                "label": _("Create from datasets"),
                "url": datasets_url
            },
            "navigation_items": navigation_items,
        })

        return context_data


class LayerFileDeleteView(DeleteView):
    # update index url to add layer__id,
    # so that we redirect to raster files list filtered to
    # this instance's layer id, the url probably used to arrive to this list
    @cached_property
    def index_url(self):
        index_url = self.url_helper.index_url
        if self.instance:
            layer_id = str(self.instance.layer.pk)
            index_url += f"?layer__id={layer_id}"

        return index_url
