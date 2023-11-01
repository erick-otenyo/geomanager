from wagtail import hooks
from wagtail_modeladmin.options import modeladmin_register

from .admin import GeoManagerAdminGroup, urls as geomanager_urls


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
