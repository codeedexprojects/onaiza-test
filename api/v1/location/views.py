from rest_framework import status
from rest_framework.decorators import (api_view, permission_classes, renderer_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from main.functions import get_auto_id
from api.v1.general.functions import generate_serializer_errors, get_user_token
from warehouses.models import Location
from api.v1.location.serializers import *


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def get_pincodes(request):
    instances = Location.objects.filter(is_deleted=False)
    serialized = LocationSerializer(instances, context={"request": request}, many=True)

    response_data = {
        "StatusCode": 6000,
        "data": serialized.data
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
@renderer_classes((JSONRenderer,))
def set_location(request):
    data = request.data
    pincode = data['pincode']

    request.session['pincode'] = pincode

    response_data = {
        "StatusCode": 6000,
        "data": pincode,
        "message": "Pincode Selected"
    }

    return Response(response_data, status=status.HTTP_200_OK)
