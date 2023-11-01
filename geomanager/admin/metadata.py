from geomanager.admin.base import BaseModelAdmin, ModelAdminCanHide
from geomanager.models import Metadata


class MetadataModelAdmin(BaseModelAdmin, ModelAdminCanHide):
    model = Metadata
    exclude_from_explorer = True
    menu_icon = 'info-circle'
