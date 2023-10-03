import uuid

from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel


class Geostore(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    iso = models.CharField(max_length=100, blank=True, null=True)
    id1 = models.CharField(max_length=100, blank=True, null=True)
    id2 = models.CharField(max_length=100, blank=True, null=True)
    id3 = models.CharField(max_length=100, blank=True, null=True)

    name_0 = models.CharField(max_length=100, blank=True, null=True)
    name_1 = models.CharField(max_length=100, blank=True, null=True)
    name_2 = models.CharField(max_length=100, blank=True, null=True)
    name_3 = models.CharField(max_length=100, blank=True, null=True)
    name_4 = models.CharField(max_length=100, blank=True, null=True)

    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.id.hex

    @property
    def bbox(self):
        min_x, min_y, max_x, max_y = self.geom.envelope.extent
        bbox = [min_x, min_y, max_x, max_y]
        return bbox

    @property
    def info(self):

        info = {}

        if self.iso:
            info.update({"iso": self.iso, "name": self.name_0})

        if self.id1:
            info.update({"id1": self.id1, "name": self.name_1})

        if self.id2:
            info.update({"id2": self.id2, "name": self.name_2})

        if self.id3:
            info.update({"id3": self.id3, "name": self.id3})

        return info
