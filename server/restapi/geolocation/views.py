from rest_framework import status, permissions
from rest_framework.response import Response
from djangorestframework_camel_case.render import CamelCaseJSONRenderer

import restapi.views
import dash.features.geolocation
import serializers


class GeolocationListView(restapi.views.RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        qpe = serializers.GeolocationQueryParamsExpectations(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        data = dash.features.geolocation.Geolocation.objects.search(**qpe.validated_data)
        serializer = serializers.GeolocationSerializer(data, many=True)
        return self.response_ok(serializer.data)
