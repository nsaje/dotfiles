from rest_framework import permissions

import restapi.common.views_base
import dash.features.geolocation
from . import serializers


class GeolocationViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        qpe = serializers.GeolocationQueryParamsExpectations(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        data = dash.features.geolocation.Geolocation.objects.search(**qpe.validated_data)
        serializer = serializers.GeolocationSerializer(data, many=True)
        return self.response_ok(serializer.data)
