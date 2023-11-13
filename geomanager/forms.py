from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms import WagtailAdminModelForm

from geomanager.models.aoi import AreaOfInterest
from geomanager.models.profile import GeoManagerUserProfile


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


class BoundaryUploadForm(forms.Form):
    remove_existing = forms.BooleanField(required=False, widget=forms.HiddenInput)
    geopackage = forms.FileField(required=True, label=_("GADM Country Geopackage"),
                                 help_text=_("The uploaded file should be a geopackage, "
                                             "downloaded from https://gadm.org/download_country.html"),
                                 widget=forms.FileInput(attrs={'accept': '.gpkg'}))


class RasterStyleModelForm(WagtailAdminModelForm):
    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return False

        use_custom_colors = self.cleaned_data.get("use_custom_colors")
        min_value = self.cleaned_data.get("min")
        max_value = self.cleaned_data.get("max")
        steps = self.cleaned_data.get("steps")
        custom_color_for_rest = self.cleaned_data.get("custom_color_for_rest")

        if max_value <= min_value:
            self.add_error("max", _("Maximum value should be greater than minimum value"))
            return False

        if min_value >= max_value:
            self.add_error("min", _("Minimum value should be less than maximum value"))
            return False

        if not use_custom_colors and not steps:
            self.add_error("steps", _("Steps required when not using custom colors"))
            return False

        if use_custom_colors:

            # no color for values greater than max
            if not custom_color_for_rest:
                self.add_error("custom_color_for_rest",
                               _("Color for the rest of values must be specified"))
                return False

            color_values_formset = self.formsets.get("color_values")

            initial_form_count = color_values_formset.initial_form_count()
            total_form_count = color_values_formset.total_form_count()
            deleted_forms_count = len(color_values_formset.deleted_forms)

            empty_forms_count = 0
            for i, form in enumerate(color_values_formset.forms):
                # Empty forms are unchanged forms beyond those with initial data.
                if not form.has_changed() and i >= initial_form_count:
                    empty_forms_count += 1

            # No custom value added
            if total_form_count - deleted_forms_count - empty_forms_count < 1:
                color_values_formset._non_form_errors = [
                    _("You selected to use custom colors but did not add any. Please add color values and save.")
                ]
                return False

            for form in color_values_formset:
                threshold = form.cleaned_data.get("threshold")

                if threshold and min_value and max_value:
                    if threshold < min_value:
                        form.add_error("threshold", _("Value must be greater than minimum defined value"))
                        return False
                    if threshold > max_value:
                        form.add_error("threshold", _("Value must be less than or equal to the maximum defined value"))
                        return False
        return True


class GeoManagerUserProfileForm(ModelForm):
    class Meta:
        model = GeoManagerUserProfile
        fields = "__all__"


class AoiForm(ModelForm):
    class Meta:
        model = AreaOfInterest
        fields = "__all__"


class VectorTableForm(forms.Form):
    columns = forms.JSONField(required=False, widget=forms.HiddenInput)
