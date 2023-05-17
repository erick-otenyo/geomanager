import os
import django
from django.conf import settings
import environ

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "geomanager"))

# reading .env file
if os.path.isfile(os.path.join(os.path.dirname(BASE_DIR), '.env')):
    environ.Env.read_env(os.path.join(os.path.dirname(BASE_DIR), '.env'))

# somehow required on my environment on mac. May not be necessary on your.
# find sample on .env.sample
GDAL_LIBRARY_PATH = env.str('GDAL_LIBRARY_PATH', None)
GEOS_LIBRARY_PATH = env.str('GEOS_LIBRARY_PATH', None)

SECRET_KEY = "django-insecure-od#(q8@gly39*2_to74w6eg78_5@*y53%w*tvgo0yvuenv-_t="

INSTALLED_APPS = [
    "geomanager",

    "wagtail",
    "taggit",

    "django.contrib.auth",
    "django.contrib.contenttypes",
]


def boot_django():
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=True,
        DATABASES={
            "default": env.db()
        },
        INSTALLED_APPS=INSTALLED_APPS,
        TIME_ZONE="UTC",
        USE_TZ=True,
        GDAL_LIBRARY_PATH=GDAL_LIBRARY_PATH,
        GEOS_LIBRARY_PATH=GEOS_LIBRARY_PATH,
        SECRET_KEY=SECRET_KEY
    )
    django.setup()
