import collections

from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import permissions

from dash.views import agency, views, helpers
from dash import regions
from dash import campaign_goals
from dash import constants
import dash.models
from utils import json_helper, exc
from .authentication import OAuth2Authentication
from utils import exc


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


class DashConstantField(serializers.Field):

    def __init__(self, const_cls, **kwargs):
        self.const_cls = const_cls
        super(DashConstantField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return getattr(self.const_cls, data)
        except AttributeError:
            self.fail('invalid_choice', data)

    def to_representation(self, value):
        return self.const_cls.get_name(value)


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
        view_internal = self.internal_view_cls(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, entity_id)
        serializer = self.serializer_cls(request, view_internal, data_internal)
        return Response(serializer.data, status=status_code)

    def put(self, request, entity_id):
        view_internal = self.internal_view_cls(rest_proxy=True)
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
        view_internal = self.internal_view_cls(rest_proxy=True)
        settings_list = self._get_settings_list(request)
        data_list_internal = [{'data': {'settings': view_internal.get_dict(request, settings, getattr(settings, 'ad_group', None) or getattr(settings, 'campaign'))}}
                              for settings in settings_list]
        serializer = self.serializer_cls(request, view_internal, data_list_internal, many=True)
        return Response(serializer.data)

    def post(self, request):
        with transaction.atomic():
            create_view_internal = self.internal_create_view_cls(rest_proxy=True)
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


class CampaignGoalsSerializer(serializers.BaseSerializer):

    def to_representation(self, data_internal):
        return {
            'id': data_internal['id'],
            'campaignId': data_internal['campaign_id'],
            'primary': data_internal['primary'],
            'type': data_internal['type'],  # TODO: convert
            'conversionGoal': self._conversion_goal_to_representation(data_internal['conversion_goal']),
            'value': data_internal['values'][-1]['value']
        }

    def _conversion_goal_to_representation(self, conversion_goal):
        if not conversion_goal:
            return conversion_goal
        return {
            'goalId': conversion_goal['goal_id'],
            'name': conversion_goal['name'],
            'pixelUrl': conversion_goal['pixel_url'],
            'conversionWindow': conversion_goal['conversion_window'],
            'type': conversion_goal['type'],  # TODO: convert
        }

    def to_internal_value(self, data_external):
        return {
            'primary': data_external['primary'],
            'type': data_external['type'],  # TODO: convert
            'conversion_goal': self._conversion_goal_to_internal_value(data_external['conversionGoal']),
            'value': data_external['value']
        }

    def _conversion_goal_to_internal_value(self, conversion_goal):
        if not conversion_goal:
            return conversion_goal
        return {
            'goal_id': conversion_goal['goalId'],
            'name': conversion_goal['name'],
            'pixel_url': conversion_goal['pixel_url'],
            'conversion_window': conversion_goal['conversionWindow'],
            'type': conversion_goal['type'],  # TODO: convert
        }


class CampaignGoalsViewList(RESTAPIBaseView):

    def get(self, request, campaign_id):
        view_internal = agency.CampaignSettings(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, campaign_id)
        serializer = CampaignGoalsSerializer(data_internal['data']['goals'], many=True)
        return Response(serializer.data)

    def post(self, request, campaign_id):
        serializer = CampaignGoalsSerializer(data=request.data)
        if serializer.is_valid():
            view_internal = agency.CampaignSettings(rest_proxy=True)
            current_settings, _ = view_internal.get(request, int(campaign_id))
            put_data = {
                'settings': current_settings['data']['settings'],
                'goals': {
                    'added': [serializer.validated_data],
                    'removed': [],
                    'primary': None,
                    'modified': {}
                }
            }
            self.request.body = RESTAPIJSONRenderer().render(put_data)
            try:
                data_internal, status_code = view_internal.put(request, int(campaign_id))
                return Response(CampaignGoalsSerializer(data_internal['data']['goals'][-1]).data)
            except exc.ValidationError as e:
                raise serializers.ValidationError(e.errors)
        return Response(serializer.errors, status=400)


class CampaignGoalPutSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=15, decimal_places=5)
    primary = serializers.BooleanField()


class CampaignGoalsViewDetails(RESTAPIBaseView):

    def get(self, request, campaign_id, goal_id):
        goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
        return Response(CampaignGoalsSerializer(goal.to_dict(with_values=True)).data)

    def put(self, request, campaign_id, goal_id):
        serializer = CampaignGoalPutSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
                value = serializer.validated_data.get('value', None)
                if value:
                    campaign_goals.add_campaign_goal_value(request, goal, value, goal.campaign)
                primary = serializer.validated_data.get('primary', None)
                if primary:
                    try:
                        campaign_goals.set_campaign_goal_primary(request, goal.campaign, goal_id)
                    except exc.ValidationError as error:
                        raise serializers.ValidationError(str(error))
                goal.refresh_from_db()
                return Response(CampaignGoalsSerializer(goal.to_dict(with_values=True)).data)
        return Response(serializer.errors, status=400)

    def delete(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        try:
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
        except dash.models.CampaignGoal.DoesNotExist:
            raise serializers.ValidationError('Goal does not exist')
        campaign_goals.delete_campaign_goal(request, goal.id, campaign)
        return Response(status=204)


class SourceIdSlugField(serializers.Field):

    def to_internal_value(self, data):
        try:
            source = dash.models.Source.objects.get(tracking_slug=data)
            return source.id
        except AttributeError:
            self.fail('invalid_choice', data)

    def to_representation(self, source):
        return source.tracking_slug


class PublisherSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=127)
    source = SourceIdSlugField()
    externalId = serializers.CharField(max_length=127, required=False, allow_null=True, source='external_id')
    status = DashConstantField(constants.PublisherStatus)
    level = DashConstantField(constants.PublisherBlacklistLevel, source='get_blacklist_level', label='level')

    def save(self, request, ad_group_id):
        post_data = {
            'state': self.validated_data['status'],
            'publishers_selected': [
                {
                    'source_id': self.validated_data['source'],
                    'domain': self.validated_data['name'],
                    'external_id': self.validated_data.get('external_id')
                }
            ],
            'publishers_not_selected': [],
            'select_all': False,
            'level': self.validated_data['get_blacklist_level']
        }
        view_internal = views.PublishersBlacklistStatus(passthrough=True)
        request.body = RESTAPIJSONRenderer().render(post_data)
        try:
            data_internal, status_code = view_internal.post(request, ad_group_id)
        except exc.ValidationError as e:
            raise serializers.ValidationError(e.errors)


class PublishersViewList(RESTAPIBaseView):

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        publishers = dash.models.PublisherBlacklist.objects.filter(
            Q(ad_group=ad_group) | Q(campaign=ad_group.campaign) | Q(account=ad_group.campaign.account)
        )
        serializer = PublisherSerializer(publishers, many=True)
        return Response(serializer.data)

    def put(self, request, ad_group_id):
        serializer = PublisherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(request, ad_group_id)
            return Response(serializer.initial_data)
        return Response(serializer.errors, status=400)
