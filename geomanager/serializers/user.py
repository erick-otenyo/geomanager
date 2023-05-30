from rest_framework import serializers
import geopandas as gpd

from geomanager.models.user import GeoManagerUser


class GeoManagerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoManagerUser
        fields = "__all__"
