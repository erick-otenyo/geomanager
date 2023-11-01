from django.urls import path

from geomanager.views import load_stations, preview_stations

urls = [
    path('load-stations/', load_stations, name='geomanager_load_stations'),
    path('preview-stations/', preview_stations, name='geomanager_preview_stations'),
]
