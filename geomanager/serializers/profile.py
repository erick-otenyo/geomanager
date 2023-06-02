from rest_framework import serializers

from geomanager.models import GeoManagerUserProfile


class GeoManagerUserProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = GeoManagerUserProfile
        fields = ["user_id", "email", "first_name", "last_name", "full_name", "gender", "country", "city", "sector",
                  "organization", "organization_type", "scale_of_operations", "position", "how_do_you_use", "interests"]

    def get_user_id(self, obj):
        return obj.user.id

    def get_email(self, obj):
        return obj.user.email

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_full_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
