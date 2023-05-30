from django.conf import settings
from django.db import models
from django.utils.text import gettext_lazy as _
from django_countries.fields import CountryField


class GeoManagerUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    gender = models.CharField(max_length=50, verbose_name=_("Gender"))
    country = CountryField(verbose_name=_("Country"))
    city = models.CharField(max_length=255, verbose_name=_("City"))
    sector = models.CharField(max_length=255, verbose_name=_("Sector"))
    organization = models.CharField(max_length=255, verbose_name=_("Organization"))
    organization_type = models.CharField(max_length=255, verbose_name=_("Organization Type"))
    scale_of_operations = models.CharField(max_length=255, verbose_name=_("Scale of Operations"))
    position = models.CharField(max_length=255, verbose_name=_("Position"))
    how_do_you_use = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("How do you Use"))
    interests = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Interests"))
