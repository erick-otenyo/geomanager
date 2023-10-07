import uuid

from django.conf import settings
from django.db import models
from django.utils.text import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from geomanager.models.geostore import Geostore


class AreaOfInterest(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    geostore_id = models.ForeignKey(Geostore, blank=True, null=True, on_delete=models.SET_NULL,
                                    verbose_name=_("Geostore Id"))
    adm_0 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Adm 0"))
    adm_1 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Adm 1"))
    adm_2 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Adm 2"))
    adm_3 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Adm 3"))
    public = models.BooleanField(default=False, verbose_name=_("Public"))
    type = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Type"))
    products = models.TextField(blank=True, null=True, verbose_name=_("Products"))
    tags = models.TextField(blank=True, null=True, verbose_name=_("Tags"))
    webhook_url = models.URLField(blank=True, null=True, verbose_name=_("Webhook Url"))

    class Meta:
        verbose_name = _("Area of Interest")
        verbose_name_plural = _("Areas of Interest")

    def __str__(self):
        return self.name
