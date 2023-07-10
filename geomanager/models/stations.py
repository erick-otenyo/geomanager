from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from wagtail.contrib.settings.models import BaseSiteSetting

from geomanager.fields import ListField
from geomanager.settings import geomanager_settings


class StationSettings(BaseSiteSetting):
    stations_table_name = "geomanager_station"

    columns = models.JSONField(blank=True, null=True)
    geom_type = models.CharField(max_length=100, blank=True, null=True)
    bounds = ListField(max_length=256, blank=True, null=True)

    @cached_property
    def full_table_name(self):
        schema = geomanager_settings.get("vector_db_schema")
        return f"{schema}.{self.stations_table_name}"

    @cached_property
    def stations_vector_tiles_url(self):
        base_url = reverse("station_tiles", args=(0, 0, 0)).replace("/0/0/0", r"/{z}/{x}/{y}")
        return base_url
