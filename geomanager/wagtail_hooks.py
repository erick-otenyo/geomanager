from adminboundarymanager.models import AdminBoundarySettings
from wagtail import hooks
from wagtail.api.v2.utils import get_full_url
from wagtail_modeladmin.options import modeladmin_register

from .admin import GeoManagerAdminGroup, urls as geomanager_urls
from .utils.boundary import create_boundary_dataset


@hooks.register('register_admin_urls')
def urlconf_geomanager():
    return geomanager_urls


modeladmin_register(GeoManagerAdminGroup)


@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        'wagtailfontawesomesvg/solid/palette.svg',
        'wagtailfontawesomesvg/solid/database.svg',
        'wagtailfontawesomesvg/solid/layer-group.svg',
        'wagtailfontawesomesvg/solid/globe.svg',
        'wagtailfontawesomesvg/solid/map.svg',
    ]


@hooks.register('construct_settings_menu')
def hide_settings_menu_item(request, menu_items):
    hidden_settings = ["admin-boundary-settings", "geomanager-settings"]
    menu_items[:] = [item for item in menu_items if item.name not in hidden_settings]


@hooks.register('register_geomanager_datasets')
def register_geomanager_datasets(request):
    datasets = []

    abm_settings = AdminBoundarySettings.for_request(request)

    boundary_tiles_url = abm_settings.boundary_tiles_url
    boundary_tiles_url = get_full_url(request, boundary_tiles_url)

    # create boundary dataset
    boundary_dataset = create_boundary_dataset(boundary_tiles_url)

    datasets.append(boundary_dataset)

    return datasets
