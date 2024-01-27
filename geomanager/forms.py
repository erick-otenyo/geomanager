from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Min
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _, gettext_lazy
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


class SelectWithDisabledOptions(forms.Select):
    """
    Subclass of Django's select widget that allows disabling options.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disabled_values = ()

    def create_option(self, name, value, *args, **kwargs):
        option_dict = super().create_option(name, value, *args, **kwargs)
        if value in self.disabled_values:
            option_dict["attrs"]["disabled"] = "disabled"
        return option_dict


class CategoryChoiceField(forms.ModelChoiceField):
    widget = SelectWithDisabledOptions

    def __init__(self, *args, disabled_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._indentation_start_depth = 2
        self.disabled_queryset = disabled_queryset

    def _get_disabled_queryset(self):
        return self._disabled_queryset

    def _set_disabled_queryset(self, queryset):
        self._disabled_queryset = queryset
        if queryset is None:
            self.widget.disabled_values = ()
        else:
            self.widget.disabled_values = queryset.values_list(
                self.to_field_name or "pk", flat=True
            )

    disabled_queryset = property(_get_disabled_queryset, _set_disabled_queryset)

    def _set_queryset(self, queryset):
        min_depth = self.queryset.aggregate(Min("depth"))["depth__min"]
        if min_depth is None:
            self._indentation_start_depth = 2
        else:
            self._indentation_start_depth = min_depth + 1

    def label_from_instance(self, obj):
        return obj.get_indented_name(self._indentation_start_depth, html=True)


class CategoryForm(WagtailAdminModelForm):
    parent = forms.ModelChoiceField(
        label=gettext_lazy("Parent"),
        queryset=None,
        required=False,
        help_text=gettext_lazy(
            "Select hierarchical position. Note: a collection cannot become a child of itself or one of its "
            "descendants."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from geomanager.models import Category

        self.fields["parent"] = CategoryChoiceField(
            label=gettext_lazy("Parent"),
            queryset=Category.objects.all(),
            required=True,
            help_text=gettext_lazy(
                "Select hierarchical position. Note: a collection cannot become a child of itself or one of its "
                "descendants."
            ),
        )

    def clean_parent(self):
        """
        Our rules about where a user may add or move a category are as follows:
            1. The user must have 'add' permission on the parent category (or its ancestors)
            2. We are not moving a category used to assign permissions for this user
            3. We are not trying to move a category to be parented by one of their descendants

        The first 2 items are taken care in the Create and Edit views by deleting the 'parent' field
        from the edit form if the user cannot move the category. This causes Django's form
        machinery to ignore the parent field for parent regardless of what the user submits.
        This methods enforces rule #3 when we are editing an existing category.
        """
        parent = self.cleaned_data["parent"]

        if not self.instance._state.adding and not parent.pk == self.initial.get(
                "parent"
        ):
            old_descendants = list(
                self.instance.get_descendants(inclusive=True).values_list(
                    "pk", flat=True
                )
            )

            if parent.pk in old_descendants:
                raise ValidationError(gettext_lazy("Please select another parent"))

        return parent
