from django import forms
from django.forms import ModelForm

from geomanager.models.aoi import AreaOfInterest


class AoiForm(ModelForm):
    class Meta:
        model = AreaOfInterest
        fields = "__all__"
