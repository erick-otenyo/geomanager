from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from geomanager.models import AreaOfInterest
from geomanager.serializers.aoi import AoiSerializer


class AoiViewSet(viewsets.ModelViewSet):
    serializer_class = AoiSerializer
    queryset = AreaOfInterest.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user.id)
        return queryset

    def create(self, request, *args, **kwargs):
        request.data.update({"user": request.user.id})

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        print(kwargs)
        return super().update(request, *args, **kwargs)
