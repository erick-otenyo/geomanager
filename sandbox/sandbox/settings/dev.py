from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-od#(q8@gly39*2_to74w6eg78_5@*y53%w*tvgo0yvuenv-_t="

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# used in dev with Mac OS
GDAL_LIBRARY_PATH = env.str('GDAL_LIBRARY_PATH', None)
GEOS_LIBRARY_PATH = env.str('GEOS_LIBRARY_PATH', None)

try:
    from .local import *
except ImportError:
    pass
