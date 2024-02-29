from django.forms import ModelForm

from geomanager.models.profile import GeoManagerUserProfile


class GeoManagerUserProfileForm(ModelForm):
    class Meta:
        model = GeoManagerUserProfile
        fields = "__all__"


