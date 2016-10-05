from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import permissions

from dash.views import agency
from utils import json_helper


class RESTAPIJSONRenderer(JSONRenderer):
    encoder_class = json_helper.JSONEncoder


class CanUseRESTAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_use_restapi'))


class RESTAPIBaseView(APIView):
    renderer_classes = [RESTAPIJSONRenderer]
    permission_classes = (permissions.IsAuthenticated, CanUseRESTAPIPermission,)


class CampaignViewDetails(RESTAPIBaseView):

    def get(self, request, campaign_id):
        view_internal = agency.CampaignSettings(passthrough=True)
        data, status_code = view_internal.get(request, campaign_id)
        return Response(data=data, status=status_code)
