from django import template

register = template.Library()


@register.simple_tag()
def get_object_attr(obj, attr):
    if hasattr(obj, attr):
        return getattr(obj, attr)
    return None
