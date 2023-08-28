# GeoManager

Wagtail based Geospatial Data Manager and backend CMS for [geomapviewer](https://github.com/wmo-raf/geomapviewer)

![Geomanager Admin Screenshot](./screenshots/geomanager_with_frontend.png)

# Background

National Meteorological and Hydrological Services (NMHSs) and other national/regional institutions working in
weather/climate sectors usually use, produce or disseminate data and information that is Geo-referenced. This can range
from forecast model outputs, earth observation data, stations observation, periodic bulletins and advisories and so on.
Usually these are shared on their websites and social media pages in static formats, mostly PNGs.

This project is an initiative by the [WMO RAF](https://github.com/wmo-raf), as part of the Digital Transformation
Package for the NMHSs in Africa, to provide an interactive system for managing and publishing Geo-referenced (GIS)
datasets. As the NMHSs produce and share their products in static formats, they can also use packages like this, to make
their data interactive.

The package is developed primarily for the NMHSs at national levels, but can be adapted in other institutions or places
that need to visualize their geospatial data.

# Features

All the raster and vector datasets uploaded must have time associated with each file.

For netCDF files with time dimension, time is automatically extracted from the file. For Geotiff, each uploaded file
must be manually assigned time.

Data management and visualization

- Uploading and visualization of gridded data
    - netCDF
    - Geotiff
- Uploading and visualization of vector data
    - Shapefiles
    - Geojson
- Raster Tile serving of raster data using [django-large-image](https://github.com/girder/django-large-image).
  All `django-large-image`features are available
- Vector tile serving using PostGIS MVT Tiles

MapViewer Management

- Management of layers visualized on the [geomapviewer](https://github.com/wmo-raf/geomapviewer)
    - Control on visibility (public or private) of layers on the MapViewer

# Installation

### Prerequisite

Before installing this package, you should make sure you have GDAL installed in your system.

`TIP:` Installing GDAL can be notoriously difficult. You can use pre-built Python wheels with the GDAL binary bundled,
provided by [KitWare](https://github.com/Kitware), for easy installation in production linux environments.

To install GDAL using KitWare GDAL wheel, use:

```shell
  pip install --find-links https://girder.github.io/large_image_wheels GDAL
```

Other required packages that you will need to install, if not installed already in your Wagtail Project

- psycopg2 - for postgres/postgis database connection

### Installation

You can install the package using pip:

```shell
pip install geomanager
```

The following packages will be automatically installed when installing `geomanager`, if not already installed.

- wagtail>=4.2.2
- wagtail-modeladmin>=1.0.0
- adm-boundary-manager>=0.0.1
- django_extensions>=3.2.1
- wagtail_color_panel>=1.4.1
- wagtailfontawesomesvg>=0.0.3,
- django_json_widget>=1.1.1
- django_nextjs>= 2.2.2
- django-allauth>=0.54.0
- django-large-image>=0.9.0
- large-image-source-gdal>=1.20.6
- large-image-source-pil>=1.20.6
- large-image-source-tiff>=1.20.6
- django-filter>=22.1
- cftime>=1.6.2
- netCDF4>=1.6.3
- rasterio>=1.3.6
- rio-cogeo>=3.5.1
- xarray>=2023.3.0
- rioxarray>=0.14.0
- shapely>=2.0.1
- djangorestframework-simplejwt>=5.2.2
- wagtail-humanitarian-icons>=1.0.3
- wagtail-icon-chooser>=0.0.1
- matplotlib>=3.7.1
- django-tables2>=2.6.0
- django-tables2-bulma-template>=0.2.0
- CairoSVG>=2.7.0
- wagtail-cache>=2.3.0
- wagtail_adminsortable=0.1

# Usage

Make sure the following are all added to your `INSTALLED_APPS` in your Wagtail `settings`

````python
INSTALLED_APPS = [
    ...

    "geomanager",
    "adminboundarymanager",
    "django_large_image",
    'django_json_widget',
    'django_nextjs',
    "django_filters",
    "wagtail_color_panel",
    "wagtail_adminsortable",
    "wagtailhumanitarianicons",
    "wagtailiconchooser",
    "django_extensions",
    "wagtailfontawesomesvg"
    "allauth",
    "allauth.account",
    "wagtailcache",
    "wagtail_modeladmin"

    "wagtail.contrib.settings",
    "rest_framework",
    "django.contrib.gis",

    ...
]

````

Run migrations

```shell
python manage.py migrate geomanager
```

Add the following to your project's `urls.py`

```python
urlpatterns = [
    ...
    path("", include("geomanager.urls")),
    ...
]
```

# Wagtail Cache Setup

Geomanager depends on the [wagtail-cache](https://github.com/coderedcorp/wagtail-cache) package for caching requests.
Please have a look at the [wagtail-cache documentation](https://docs.coderedcorp.com/wagtail-cache/) for setup
instructions

# Including the Map Viewer

This package is the backend component to the frontend [geomapviewer](https://github.com/wmo-raf/geomapviewer).

# Documentation

TODO
