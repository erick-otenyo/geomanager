from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class EmailTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        raw_username = attrs["username"]
        user = get_user_model().objects.filter(email=raw_username)
        if user:
            user = user.first()
            attrs['username'] = user.username

        data = super().validate(attrs)
        return data


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=get_user_model().objects.all(), message="User with this email already exists")]
    )

    class Meta:
        model = get_user_model()
        fields = ('username',)


class ResetPasswordSerializer(serializers.ModelSerializer):
    username = serializers.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ('username',)

    def validate_username(self, value):
        try:
            get_user_model().objects.get(email=value)
            return value
        except ObjectDoesNotExist:
            raise ValidationError("User with this email does not exists")
