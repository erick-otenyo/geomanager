from django import template

register = template.Library()


@register.simple_tag()
def get_object_attr(obj, attr):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    return None


@register.inclusion_tag("geomanager/shared/breadcrumbs.html")
def breadcrumbs_component(items, is_expanded=True, classname=None):
    return {"items": items, "is_expanded": is_expanded, "classname": classname}
