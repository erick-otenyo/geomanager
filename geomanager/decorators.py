from functools import wraps

from django.utils.cache import patch_cache_control


def revalidate_cache(view_func):
    """
    Decorator that adds must_revalidate header to a response
    """

    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        # Ensure argument looks like a request.
        if not hasattr(request, "META"):
            raise TypeError(
                "revalidate_cache didn't receive an HttpRequest. If you are "
                "decorating a classmethod, be sure to use @method_decorator."
            )
        response = view_func(request, *args, **kwargs)
        patch_cache_control(response, must_revalidate=True)
        return response

    return _wrapped_view_func
