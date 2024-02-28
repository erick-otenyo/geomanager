from django import forms
from django.utils.translation import gettext_lazy as _


class VectorLayerFileForm(forms.Form):
    layer = forms.ModelChoiceField(required=True, queryset=None, empty_label=None, label=_("layer"))
    time = forms.DateTimeField(required=True,
                               widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, ),
                               localize=False,
                               label=_("time"),
                               help_text=_("Time is required for every uploaded vector file. "
                                           "This can be the time the dataset was collected, or applies to."))
    table_name = forms.CharField(required=True, label=_("database table name"))
    description = forms.CharField(required=False, widget=forms.Textarea, label=_("dataset description"),
                                  help_text=_("optional dataset description"))

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset', None)
        super().__init__(*args, **kwargs)
        self.fields['layer'].queryset = queryset


