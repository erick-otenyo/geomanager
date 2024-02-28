from django import forms
from django.utils.translation import gettext_lazy as _


class LayerRasterFileForm(forms.Form):
    layer = forms.ModelChoiceField(required=True, queryset=None, empty_label=None, label=_("layer"), )
    time = forms.DateTimeField(required=True,
                               widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, ),
                               localize=False, label=_("time"),
                               help_text=_("Time for the raster file. This can be the time the data was acquired, "
                                           "or the date and time for which the data applies"))
    nc_dates = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple, label=_("NetCDF Dates"),
                                         help_text=_("Timestamps in the dataset"))
    nc_data_variable = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, nc_dates_choices=None, *args, **kwargs):

        queryset = kwargs.pop('queryset', None)
        super().__init__(*args, **kwargs)
        self.fields['layer'].queryset = queryset

        if nc_dates_choices:
            self.fields['nc_dates'].choices = [(choice, choice) for choice in nc_dates_choices]

            # hide time input
            self.fields['time'].widget = forms.HiddenInput()
            self.fields['time'].required = False
        else:
            self.fields['nc_dates'].widget = forms.HiddenInput()
