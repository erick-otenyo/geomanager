from django.contrib.admin.utils import quote
from django.urls import reverse
from django.utils.translation import gettext as _
from wagtail.contrib.modeladmin.helpers import ButtonHelper, AdminURLHelper


class CategoryButtonHelper(ButtonHelper):
    def get_buttons_for_obj(
            self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        buttons = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        classnames = self.edit_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)

        create_dataset_button = {
            "url": obj.dataset_create_url(),
            "label": _("Create Dataset"),
            "classname": cn,
            "title": _("Create Dataset") % {"object": self.verbose_name},
        }

        buttons.append(create_dataset_button)

        return buttons


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
                "title": _("Add Layer ") % {"object": self.verbose_name},
            }
            buttons.append(create_layer_button)

        return buttons


class FileLayerButtonHelper(ButtonHelper):
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


def get_layer_action_url(layer_type, action, action_args=None):
    if layer_type == "file":
        from geomanager.models import FileImageLayer
        file_layer_admin_helper = AdminURLHelper(FileImageLayer)
        url = file_layer_admin_helper.get_action_url(action, action_args)
    elif layer_type == "wms":
        from geomanager.models.raster import WmsLayer
        wms_layer_admin_helper = AdminURLHelper(WmsLayer)
        url = wms_layer_admin_helper.get_action_url(action, action_args)
    elif layer_type == "vector":
        from geomanager.models.vector import VectorLayer
        vector_layer_admin_helper = AdminURLHelper(VectorLayer)
        url = vector_layer_admin_helper.get_action_url(action, action_args)
    else:
        url = None

    return url


def get_preview_url(layer_type, dataset_id, layer_id=None):
    args = [quote(dataset_id)]
    if layer_id:
        args.append(layer_id)

    if layer_type == "file":
        if layer_id:
            preview_url = reverse(
                f"geomanager_preview_raster_layer",
                args=args,
            )
        else:
            preview_url = reverse(
                f"geomanager_preview_raster_dataset",
                args=args,
            )
    elif layer_type == "vector":
        if layer_id:
            preview_url = reverse(
                f"geomanager_preview_vector_layer",
                args=args,
            )
        else:
            preview_url = reverse(
                f"geomanager_preview_vector_dataset",
                args=args,
            )

    elif layer_type == "wms":
        if layer_id:
            preview_url = reverse(
                f"geomanager_preview_wms_layer",
                args=args,
            )
        else:
            preview_url = reverse(
                f"geomanager_preview_wms_dataset",
                args=args,
            )

    else:
        preview_url = None

    return preview_url


def get_upload_url(layer_type, dataset_id, layer_id=None):
    args = [quote(dataset_id)]
    if layer_id:
        args.append(layer_id)

    if layer_type == "file":
        if layer_id:
            upload_url = reverse(
                f"geomanager_dataset_layer_upload_raster",
                args=args,
            )
        else:
            upload_url = reverse(
                f"geomanager_dataset_upload_raster",
                args=args,
            )
    elif layer_type == "vector":
        if layer_id:
            upload_url = reverse(
                f"geomanager_dataset_layer_upload_vector",
                args=args,
            )
        else:
            upload_url = reverse(
                f"geomanager_dataset_upload_vector",
                args=args,
            )
    else:
        upload_url = None

    return upload_url


def get_raster_layer_files_url(layer_id=None):
    from geomanager.models import LayerRasterFile
    admin_helper = AdminURLHelper(LayerRasterFile)
    url = admin_helper.get_action_url("index")

    if layer_id:
        url = url + f"?layer__id={layer_id}"

    return url


def get_vector_layer_files_url(layer_id=None):
    from geomanager.models import PgVectorTable
    admin_helper = AdminURLHelper(PgVectorTable)
    url = admin_helper.get_action_url("index")

    if layer_id:
        url = url + f"?layer__id={layer_id}"

    return url
