from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import AllowAny

from geomanager.serializers import RegisterSerializer, ResetPasswordSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class ResetPasswordView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer
