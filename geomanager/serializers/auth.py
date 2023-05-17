from allauth.account.forms import ResetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        model = User
        fields = ('email',)

    def create(self, validated_data):
        request = self.context.get("request")

        user = User.objects.create(
            username=validated_data['email'],
            email=validated_data['email']
        )

        user.save()

        form = ResetPasswordForm({"email": user.email})
        if form.is_valid():
            form.save(request)

        return user


class ResetPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email',)

    def create(self, validated_data):
        request = self.context.get("request")

        username = validated_data['email']

        try:
            user = User.objects.get(username=username)
            form = ResetPasswordForm({"email": user.email})
            if form.is_valid():
                form.save(request)

            return user

        except ObjectDoesNotExist:
            raise ValidationError({"email": "User with this email does not exist"})
