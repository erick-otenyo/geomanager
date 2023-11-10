from django.urls import path

from .views import StationsTileView

urlpatterns = [
    path(r'api/station-tiles/<int:z>/<int:x>/<int:y>', StationsTileView.as_view(), name="station_tiles"),
]
