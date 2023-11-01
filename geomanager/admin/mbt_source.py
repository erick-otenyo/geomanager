from django.utils.translation import gettext_lazy as _

from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide
from geomanager.models import MBTSource


class MBTSourceModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = MBTSource
    menu_label = _("Basemap Sources")
    menu_icon = "globe"
    form_view_extra_js = ["geomanager/js/mbt_source_extra.js"]
