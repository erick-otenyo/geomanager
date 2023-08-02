from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from geomanager.forms import GeoManagerUserProfileForm
from geomanager.models import GeoManagerUserProfile
from geomanager.serializers.profile import GeoManagerUserProfileSerializer


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def get_geomanager_user_profile(request, user_id):
    try:
        profile = GeoManagerUserProfile.objects.get(user=user_id)
    except ObjectDoesNotExist:
        return Response({"detail": "Profile does not exist for user"}, status=404)

    serializer = GeoManagerUserProfileSerializer(profile)

    return Response(serializer.data)


@api_view(['PATCH'])
@renderer_classes([JSONRenderer])
def create_or_update_geomanager_user_profile(request, user_id):
    try:
        profile = GeoManagerUserProfile.objects.get(user=user_id)
    except ObjectDoesNotExist:
        profile = None

    try:
        user = get_user_model().objects.get(id=user_id)
    except ObjectDoesNotExist:
        return Response({"detail": "User does not exist"}, status=404)

    user_data_fields = ["first_name", "last_name"]

    data = request.data
    data.update({"user": user_id})

    if profile:
        form = GeoManagerUserProfileForm(request.data, instance=profile)
    else:
        form = GeoManagerUserProfileForm(request.data)

    if form.is_valid():
        profile = form.save()
        user_data = {}
        for key, value in request.data.items():
            if key in user_data_fields and value:
                user_data.update({key: value})
        if user_data:
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()

        profile.user = user
        serializer = GeoManagerUserProfileSerializer(profile)

        return Response(serializer.data)

    return Response({"detail": "Error occurred. Please try again later"}, status=400)
