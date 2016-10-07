import collections

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import permissions

from dash.views import agency, views
from dash import regions
import dash.models
from utils import json_helper
from .authentication import OAuth2Authentication


class NotProvided(object):
    def __getitem__(self, key):
        return self
NOT_PROVIDED = NotProvided()


class RESTAPIJSONRenderer(JSONRenderer):
    encoder_class = json_helper.JSONEncoder


class CanUseRESTAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_use_restapi'))


class RESTAPIBaseView(APIView):
    authentication_classes = [OAuth2Authentication]
    renderer_classes = [RESTAPIJSONRenderer]
    permission_classes = (permissions.IsAuthenticated, CanUseRESTAPIPermission,)


class SettingsSerializer(serializers.BaseSerializer):

    def __init__(self, request, view_internal, *args, **kwargs):
        self.request = request
        self.view_internal = view_internal
        super(SettingsSerializer, self).__init__(*args, **kwargs)

    def update(self, data_internal, validated_data):
        settings = data_internal['data']['settings']
        entity_id = int(settings['id'])
        settings.update(validated_data['settings'])
        self.request.body = RESTAPIJSONRenderer().render(({'settings': settings}))
        try:
            data_internal_new, _ = self.view_internal.put(self.request, entity_id)
        except Exception as e:
            raise serializers.ValidationError(e.errors)
        return data_internal_new

    @classmethod
    def many_init(cls, request, view_internal, *args, **kwargs):
        kwargs['child'] = cls(request, view_internal, *args, **kwargs)
        return serializers.ListSerializer(*args, **kwargs)


class CampaignSerializer(SettingsSerializer):

    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        return {
            'id': settings['id'],
            # 'accountId': settings['account_id'],
            'name': settings['name'],
            'campaignManager': settings['campaign_manager'],
            'tracking': {
                'ga': {
                    'enabled': settings['enable_ga_tracking'],
                    'type': settings['ga_tracking_type'],
                    'webPropertyId': settings['ga_property_id'],
                },
                'adobe': {
                    'enabled': settings['enable_adobe_tracking'],
                    'trackingParameter': settings['adobe_tracking_param'],
                },
            },
        }

    def to_internal_value(self, external_data):
        data = collections.defaultdict(lambda: NOT_PROVIDED)
        data.update(external_data)
        settings = {
            'id': data['id'],
            'account_id': data['accountId'],
            'name': data['name'],
            'campaign_manager': data['campaignManager'],
            'enable_ga_tracking': data['tracking']['ga']['enabled'],
            'ga_tracking_type': data['tracking']['ga']['type'],
            'ga_property_id': data['tracking']['ga']['webPropertyId'],
            'enable_adobe_tracking': data['tracking']['adobe']['enabled'],
            'adobe_tracking_param': data['tracking']['adobe']['trackingParameter'],
        }
        return {'settings': {k: v for k, v in settings.items() if v != NOT_PROVIDED}}


class AdGroupSerializer(SettingsSerializer):
    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        return {
            'id': settings['id'],
            # 'campaignId': settings['campaign_id'],
            'name': settings['name'],
            'state': settings['state'],
            'startDate': settings['start_date'],
            'endDate': settings['end_date'],
            'maxCpc': settings['cpc_cc'],
            'dailyBudget': settings['daily_budget_cc'],
            'trackingCode': settings['tracking_code'],
            'targeting': {
                'geo': {
                    'included': self._partition_regions(settings['target_regions']),
                },
                'devices': settings['target_devices'],
            },
            'autopilot': {
                'state': settings['autopilot_state'],
                'dailyBudget': settings['autopilot_daily_budget'],
            },
        }

    def to_internal_value(self, external_data):
        data = collections.defaultdict(lambda: NOT_PROVIDED)
        data.update(external_data)
        settings = {
            'id': data['id'],
            'campaign_id': data['campaignId'],
            'name': data['name'],
            'state': data['state'],
            'start_date': data['startDate'],
            'end_date': data['endDate'],
            'cpc_cc': data['maxCpc'],
            'daily_budget_cc': data['dailyBudget'],
            'tracking_code': data['trackingCode'],
            'target_regions': self._unpartition_regions(data['targeting']['geo']['included']),
            'target_devices': data['targeting']['devices'],
            'autopilot_state': data['autopilot']['state'],
            'autopilot_daily_budget': data['autopilot']['dailyBudget'],
        }
        return {'settings': {k: v for k, v in settings.items() if v != NOT_PROVIDED}}

    @staticmethod
    def _partition_regions(target_regions):
        geo = {
            'countries': [],
            'regions': [],
            'dma': []
        }
        for region in target_regions:
            if region in regions.COUNTRY_BY_CODE:
                geo['countries'].append(region)
            elif region in regions.SUBDIVISION_BY_CODE:
                geo['regions'].append(region)
            elif region in regions.DMA_BY_CODE:
                geo['dma'].append(region)
            else:
                raise Exception('Unknown region returned from internal API!')
        return geo

    @staticmethod
    def _unpartition_regions(geo):
        if geo == NOT_PROVIDED:
            return NOT_PROVIDED
        target_regions = []
        target_regions.extend(geo['countries'])
        target_regions.extend(geo['regions'])
        target_regions.extend(geo['dma'])
        return target_regions


class SettingsViewDetails(RESTAPIBaseView):

    def get(self, request, entity_id):
        view_internal = self.internal_view_cls(passthrough=True)
        data_internal, status_code = view_internal.get(request, entity_id)
        serializer = self.serializer_cls(request, view_internal, data_internal)
        return Response(serializer.data, status=status_code)

    def put(self, request, entity_id):
        view_internal = self.internal_view_cls(passthrough=True)
        data_internal, status_code = view_internal.get(request, entity_id)
        serializer = self.serializer_cls(request, view_internal, data_internal, request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class SettingsViewList(RESTAPIBaseView):

    def _get_settings_list(self, request):
        raise NotImplementedError()

    def get(self, request):
        view_internal = self.internal_view_cls(passthrough=True)
        settings_list = self._get_settings_list(request)
        data_list_internal = [{'data': {'settings': view_internal.get_dict(request, settings, getattr(settings, 'ad_group', None) or getattr(settings, 'campaign'))}}
                              for settings in settings_list]
        serializer = self.serializer_cls(request, view_internal, data_list_internal, many=True)
        return Response(serializer.data)

    def post(self, request):
        with transaction.atomic():
            create_view_internal = self.internal_create_view_cls(passthrough=True)
            parent_id = request.data[self.parent_id_field]
            try:
                data_internal, status_code = create_view_internal.put(request, int(parent_id))
            except Exception as e:
                raise serializers.ValidationError(e.errors)
            entity_id = data_internal['data']['id']
            response = self.details_view_cls().put(request, entity_id)
            if response.status_code != 201:
                transaction.set_rollback(True)
            return response


class CampaignViewDetails(SettingsViewDetails):
    internal_view_cls = agency.CampaignSettings
    serializer_cls = CampaignSerializer


class CampaignViewList(SettingsViewList):
    internal_view_cls = agency.CampaignSettings
    internal_create_view_cls = views.AccountCampaigns
    serializer_cls = CampaignSerializer
    details_view_cls = CampaignViewDetails
    parent_id_field = 'accountId'

    def _get_settings_list(self, request):
        account_id = request.query_params.get('accountId', None)
        campaigns = dash.models.Campaign.objects.all().filter_by_user(request.user)
        campaign_settings = dash.models.CampaignSettings.objects.filter(campaign__in=campaigns).group_current_settings().select_related('campaign')
        if account_id:
            campaign_settings = campaign_settings.filter(campaign__account_id=int(account_id))
        return campaign_settings


class AdGroupViewDetails(SettingsViewDetails):
    internal_view_cls = agency.AdGroupSettings
    serializer_cls = AdGroupSerializer


class AdGroupViewList(SettingsViewList):
    internal_view_cls = agency.AdGroupSettings
    internal_create_view_cls = views.CampaignAdGroups
    serializer_cls = AdGroupSerializer
    details_view_cls = AdGroupViewDetails
    parent_id_field = 'campaignId'

    def _get_settings_list(self, request):
        campaign_id = request.query_params.get('campaignId', None)
        ad_groups = dash.models.AdGroup.objects.all().filter_by_user(request.user)
        ag_settings = dash.models.AdGroupSettings.objects.filter(ad_group__in=ad_groups).group_current_settings().select_related('ad_group')
        if campaign_id:
            ag_settings = ag_settings.filter(ad_group__campaign_id=int(campaign_id))
        return ag_settings
