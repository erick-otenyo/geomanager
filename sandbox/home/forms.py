from django import forms
from django.utils.translation import gettext_lazy as _


class StationsUploadForm(forms.Form):
    shp_zip = forms.FileField(required=True, label=_("Stations Shapefile ZIP"),
                              widget=forms.FileInput(attrs={'accept': '.zip'}))


class StationColumnsForm(forms.Form):
    columns = forms.JSONField(required=False, widget=forms.HiddenInput)
    name_column = forms.ChoiceField(required=False, label=_("Station name field"))

    def __init__(self, *args, **kwargs):
        column_choices = None
        if "column_choices" in kwargs:
            column_choices = kwargs.get("column_choices")
            kwargs.pop("column_choices")

        super().__init__(*args, **kwargs)

        if column_choices:
            choices = [("", "--------")]
            choices.extend(column_choices)
            self.fields['name_column'].choices = choices
        else:
            self.fields['name_column'].widget = forms.HiddenInput()
