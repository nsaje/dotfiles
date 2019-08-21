import rest_framework.permissions

import restapi.conversion_pixel.v1.views

from . import serializers


class ConversionPixelViewSet(restapi.conversion_pixel.v1.views.ConversionPixelViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.ConversionPixelSerializer
    create_serializer = serializers.ConversionPixelCreateSerializer
