from rest_framework import serializers

from geomanager.models.aoi import AreaOfInterest


class AoiSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()

    class Meta:
        model = AreaOfInterest
        fields = ["id", "user", "email", "name", "geostore_id", "adm_0", "adm_1", "adm_2", "adm_3", "public", "type",
                  "tags", "webhook_url"]

    def to_representation(self, instance):
        aoi = super().to_representation(instance)
        if aoi.get("tags"):
            aoi["tags"] = aoi["tags"].split(",")
        return aoi

    def get_email(self, obj):
        return obj.user.email
