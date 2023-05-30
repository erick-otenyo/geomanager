from rest_framework import viewsets

from geomanager.models.user import GeoManagerUser
from geomanager.serializers.user import GeoManagerUserSerializer


class GeoManagerUserViewSet(viewsets.ModelViewSet):
    queryset = GeoManagerUser.objects.all()
    serializer_class = GeoManagerUserSerializer
