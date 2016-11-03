import collections
import logging
import influx

from django.db import transaction
from django.db.models import Q
import django.db.models
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import permissions
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from djangorestframework_camel_case.parser import CamelCaseJSONParser

from dash.views import agency, views, bcm, helpers
from dash import regions
from dash import campaign_goals
from dash import constants
from dash import upload
import dash.models
import dash.threads
from utils import json_helper, exc, dates_helper
from .authentication import OAuth2Authentication
import restapi.models
import restapi.reports


logger = logging.getLogger(__name__)


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

    def dispatch(self, request, *args, **kwargs):
        with influx.block_timer('restapi.request', endpoint=self.__class__.__name__, method=request.method):
            return super(RESTAPIBaseView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def response_ok(data, errors=None, **kwargs):
        data = {'data': data}
        if errors:
            data['errors'] = errors
        return Response(data, **kwargs)


class IdField(serializers.Field):
    def to_representation(self, data):
        if isinstance(data, django.db.models.Model):
            return str(data.id)
        return str(data)

    def to_internal_value(self, data):
        return int(data)


class DashConstantField(serializers.Field):

    def __init__(self, const_cls, **kwargs):
        self.const_cls = const_cls
        super(DashConstantField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        if data == NOT_PROVIDED:
            return NOT_PROVIDED
        try:
            return getattr(self.const_cls, data)
        except AttributeError:
            valid_choices = self.const_cls.get_all_names()
            raise serializers.ValidationError('Invalid choice %s! Valid choices: %s' % (data, ', '.join(valid_choices)))

    def to_internal_value_many(self, data):
        if data == NOT_PROVIDED:
            return NOT_PROVIDED
        return map(lambda x: self.to_internal_value(x), data)

    def to_representation(self, value):
        return self.const_cls.get_name(value)

    def to_representation_many(self, data):
        return map(lambda x: self.to_representation(x), data)


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
        data_internal_new, _ = self.view_internal.put(self.request, entity_id)
        return data_internal_new

    @classmethod
    def many_init(cls, request, view_internal, *args, **kwargs):
        kwargs['child'] = cls(request, view_internal, *args, **kwargs)
        return serializers.ListSerializer(*args, **kwargs)

    @classmethod
    def _allow_not_provided(cls, d):
        if d == NOT_PROVIDED:
            return NOT_PROVIDED
        new_dict = collections.defaultdict(lambda: NOT_PROVIDED)
        new_dict.update(d)
        for key, value in new_dict.items():
            if isinstance(value, dict):
                new_dict[key] = cls._allow_not_provided(value)
        return new_dict


class AccountCreditSerializer(serializers.Serializer):

    def to_representation(self, internal_data):
        return {
            'id': str(internal_data['id']),
            'createdOn': internal_data['created_on'],
            'startDate': internal_data['start_date'],
            'endDate': internal_data['end_date'],
            'total': internal_data['total'],
            'allocated': internal_data['allocated'],
            'available': internal_data['available'],
        }


class AccountCreditViewList(RESTAPIBaseView):

    def get(self, request, account_id):
        internal_view = bcm.AccountCreditView(rest_proxy=True)
        data_internal, _ = internal_view.get(self.request, account_id)
        serializer = AccountCreditSerializer(data_internal['data']['active'], many=True)
        return self.response_ok(serializer.data)


class CampaignSerializer(SettingsSerializer):

    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        return {
            'id': settings['id'],
            'accountId': settings['account_id'],
            'name': settings['name'],
            # 'campaignManager': self._user_to_email(settings['campaign_manager']),  # TODO(nsaje): convert to email
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
        data = self._allow_not_provided(external_data)
        settings = {
            'id': data['id'],
            'name': data['name'],
            # 'campaign_manager': data['campaignManager'],  # TODO(nsaje): convert from email
            'enable_ga_tracking': data['tracking']['ga']['enabled'],
            'ga_tracking_type': data['tracking']['ga']['type'],
            'ga_property_id': data['tracking']['ga']['webPropertyId'],
            'enable_adobe_tracking': data['tracking']['adobe']['enabled'],
            'adobe_tracking_param': data['tracking']['adobe']['trackingParameter'],
        }
        return {'settings': {k: v for k, v in settings.items() if v != NOT_PROVIDED}}


class AdGroupSerializer(SettingsSerializer):

    def update(self, data_internal, validated_data):
        """ Handle state update separately, since it's on a separate endpoint """
        settings = data_internal['data']['settings']
        validated_settings = validated_data['settings']
        if validated_settings.get('state') and validated_settings['state'] != settings['state']:
            entity_id = int(settings['id'])
            self.request.body = RESTAPIJSONRenderer().render(({'state': validated_settings['state']}))
            internal_view = agency.AdGroupSettingsState(rest_proxy=True)
            data_internal_new, _ = internal_view.post(self.request, entity_id)

        data_internal_new = super(AdGroupSerializer, self).update(data_internal, validated_data)
        return data_internal_new

    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        return {
            'id': settings['id'],
            'campaignId': settings['campaign_id'],
            'name': settings['name'],
            'state': constants.AdGroupSettingsState.get_name(settings['state']),
            'startDate': settings['start_date'],
            'endDate': settings['end_date'],
            'maxCpc': settings['cpc_cc'],
            'dailyBudget': settings['daily_budget_cc'],
            'trackingCode': settings['tracking_code'],
            'targeting': {
                'geo': {
                    'included': self._partition_regions(settings['target_regions']),
                },
                'devices': map(lambda x: DashConstantField(constants.AdTargetDevice).to_representation(x), settings['target_devices']),
                'interest': {
                    'included': map(lambda x: DashConstantField(constants.InterestCategory).to_representation(x), settings['interest_targeting']),
                    'excluded': map(lambda x: DashConstantField(constants.InterestCategory).to_representation(x), settings['exclusion_interest_targeting']),
                }
            },
            'autopilot': {
                'state': constants.AdGroupSettingsAutopilotState.get_name(settings['autopilot_state']),
                'dailyBudget': settings['autopilot_daily_budget'],
            },
        }

    def to_internal_value(self, external_data):
        data = self._allow_not_provided(external_data)
        settings = {
            'id': data['id'],
            'name': data['name'],
            'state': DashConstantField(constants.AdGroupSettingsState).to_internal_value(data['state']),
            'start_date': data['startDate'],
            'end_date': data['endDate'],
            'cpc_cc': data['maxCpc'],
            'daily_budget_cc': data['dailyBudget'],
            'tracking_code': data['trackingCode'],
            'target_regions': self._unpartition_regions(data['targeting']['geo']['included']),
            'target_devices': DashConstantField(constants.AdTargetDevice).to_internal_value_many(data['targeting']['devices']),
            'interest_targeting': DashConstantField(constants.InterestCategory).to_internal_value_many(data['targeting']['interest']['included']),
            'exclusion_interest_targeting': DashConstantField(constants.InterestCategory).to_internal_value_many(data['targeting']['interest']['excluded']),
            'autopilot_state': DashConstantField(constants.AdGroupSettingsAutopilotState).to_internal_value_many(data['autopilot']['state']),
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
        return self.response_ok(serializer.data, status=status_code)

    def put(self, request, entity_id):
        view_internal = self.internal_view_cls(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, entity_id)
        serializer = self.serializer_cls(request, view_internal, data_internal, request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.response_ok(serializer.data, status=201)


class SettingsViewList(RESTAPIBaseView):

    def _get_settings_list(self, request):
        raise NotImplementedError()

    def get(self, request):
        view_internal = self.internal_view_cls(rest_proxy=True)
        settings_list = self._get_settings_list(request)
        data_list_internal = [{'data': {'settings': view_internal.get_dict(request, settings, getattr(settings, 'ad_group', None) or getattr(settings, 'campaign'))}}
                              for settings in settings_list]
        serializer = self.serializer_cls(request, view_internal, data_list_internal, many=True)
        return self.response_ok(serializer.data)

    def post(self, request):
        with transaction.atomic():
            create_view_internal = self.internal_create_view_cls(rest_proxy=True)
            parent_id = request.data.get(self.parent_id_field)
            if not parent_id:
                raise serializers.ValidationError({self.parent_id_field: 'required'})
            data_internal, status_code = create_view_internal.put(request, int(parent_id))
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
            'type': constants.CampaignGoalKPI.get_name(data_internal['type']),
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
            'type': constants.ConversionGoalType.get_name(conversion_goal['type']),
        }

    def to_internal_value(self, data_external):
        try:
            return {
                'primary': data_external['primary'],
                'type': DashConstantField(constants.CampaignGoalKPI).to_internal_value(data_external['type']),
                'conversion_goal': self._conversion_goal_to_internal_value(data_external['conversionGoal']),
                'value': data_external['value']
            }
        except KeyError as e:
            raise serializers.ValidationError({e.message: 'missing'})

    def _conversion_goal_to_internal_value(self, conversion_goal):
        if not conversion_goal:
            return conversion_goal
        return {
            'goal_id': conversion_goal['goalId'],
            'name': conversion_goal['name'],
            'pixel_url': conversion_goal['pixel_url'],
            'conversion_window': conversion_goal['conversionWindow'],
            'type': DashConstantField(constants.ConversionGoalType).to_internal_value(conversion_goal['type']),
        }


class CampaignGoalsViewList(RESTAPIBaseView):

    def get(self, request, campaign_id):
        view_internal = agency.CampaignSettings(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, campaign_id)
        serializer = CampaignGoalsSerializer(data_internal['data']['goals'], many=True)
        return self.response_ok(serializer.data)

    def post(self, request, campaign_id):
        serializer = CampaignGoalsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
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
        data_internal, status_code = view_internal.put(request, int(campaign_id))
        return self.response_ok(CampaignGoalsSerializer(data_internal['data']['goals'][-1]).data)


class CampaignGoalPutSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=15, decimal_places=5)
    primary = serializers.BooleanField()


class CampaignGoalsViewDetails(RESTAPIBaseView):

    def get(self, request, campaign_id, goal_id):
        goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
        return self.response_ok(CampaignGoalsSerializer(goal.to_dict(with_values=True)).data)

    def put(self, request, campaign_id, goal_id):
        serializer = CampaignGoalPutSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
            value = serializer.validated_data.get('value', None)
            if value:
                campaign_goals.add_campaign_goal_value(request, goal, value, goal.campaign)
            primary = serializer.validated_data.get('primary', None)
            if primary:
                campaign_goals.set_campaign_goal_primary(request, goal.campaign, goal_id)
            goal.refresh_from_db()
            return self.response_ok(CampaignGoalsSerializer(goal.to_dict(with_values=True)).data)

    def delete(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        try:
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
        except dash.models.CampaignGoal.DoesNotExist:
            raise exc.MissingDataError('Goal does not exist')
        campaign_goals.delete_campaign_goal(request, goal.id, campaign)
        return self.response_ok(status=204)


class CampaignBudgetSerializer(serializers.Serializer):
    id = IdField(read_only=True)
    creditId = IdField(source='credit', write_only=True)
    amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')
    state = DashConstantField(constants.BudgetLineItemState, read_only=True)
    spend = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    available = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)


class CampaignBudgetViewList(RESTAPIBaseView):

    def get(self, request, campaign_id):
        internal_view = bcm.CampaignBudgetView(rest_proxy=True)
        data_internal, _ = internal_view.get(self.request, campaign_id)

        # different field name for post and get
        for d in data_internal['data']['active']:
            d['amount'] = d['total']
            del d['total']

        serializer = CampaignBudgetSerializer(data_internal['data']['active'], many=True)
        return self.response_ok(serializer.data)

    def post(self, request, campaign_id):
        serializer = CampaignBudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        internal_view = bcm.CampaignBudgetView(rest_proxy=True)
        post_data = serializer.validated_data

        self.request.body = RESTAPIJSONRenderer().render(post_data)
        data_internal, _ = internal_view.put(self.request, campaign_id)
        budget_id = int(data_internal['data'])
        return CampaignBudgetViewDetails().get(self.request, campaign_id, budget_id)


class CampaignBudgetViewDetails(RESTAPIBaseView):

    def get(self, request, campaign_id, budget_id):
        internal_view = bcm.CampaignBudgetItemView(rest_proxy=True)
        data_internal, _ = internal_view.get(request, campaign_id, budget_id)
        serializer = CampaignBudgetSerializer(data_internal['data'])
        return self.response_ok(serializer.data)

    def put(self, request, campaign_id, budget_id):
        internal_view = bcm.CampaignBudgetItemView(rest_proxy=True)

        data_internal_get, _ = internal_view.get(request, campaign_id, budget_id)
        serializer = CampaignBudgetSerializer(instance=data_internal_get['data'], data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        put_data = {k: data_internal_get['data'][k] for k in ['credit', 'amount', 'start_date', 'end_date', 'comment']}
        put_data['credit'] = put_data['credit']['id']
        put_data.update(serializer.validated_data)
        self.request.body = RESTAPIJSONRenderer().render(put_data)
        internal_view.post(self.request, campaign_id, budget_id)
        return CampaignBudgetViewDetails().get(self.request, campaign_id, budget_id)


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
        view_internal = views.PublishersBlacklistStatus(rest_proxy=True)
        request.body = RESTAPIJSONRenderer().render(post_data)
        data_internal, status_code = view_internal.post(request, ad_group_id)


class PublishersViewList(RESTAPIBaseView):

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        publishers = dash.models.PublisherBlacklist.objects.filter(
            Q(ad_group=ad_group) | Q(campaign=ad_group.campaign) | Q(account=ad_group.campaign.account)
        )
        serializer = PublisherSerializer(publishers, many=True)
        return self.response_ok(serializer.data)

    def put(self, request, ad_group_id):
        serializer = PublisherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request, ad_group_id)
        return self.response_ok(serializer.initial_data)


class AdGroupSourceSerializer(serializers.Serializer):
    source = SourceIdSlugField(source='ad_group_source.source')
    cpc = serializers.DecimalField(max_digits=10, decimal_places=4, source='cpc_cc')
    dailyBudget = serializers.DecimalField(max_digits=10, decimal_places=4, source='daily_budget_cc')
    state = DashConstantField(constants.AdGroupSourceSettingsState)

    def create(self, validated_data):
        request = validated_data['request']
        ad_group_id = validated_data['ad_group_id']
        source_id = validated_data['ad_group_source']['source']
        put_data = {field: validated_data[field] for field in ['cpc_cc', 'daily_budget_cc', 'state'] if field in validated_data}
        request.body = RESTAPIJSONRenderer().render(put_data)
        view_internal = views.AdGroupSourceSettings(rest_proxy=True)
        data_internal, status_code = view_internal.put(request, ad_group_id, source_id)


class AdGroupSourcesViewList(RESTAPIBaseView):

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        settings = dash.models.AdGroupSourceSettings.objects.filter(ad_group_source__ad_group=ad_group).group_current_settings()
        serializer = AdGroupSourceSerializer(settings, many=True)
        return self.response_ok(serializer.data)

    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        serializer = AdGroupSourceSerializer(data=request.data, many=True, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request, ad_group_id=ad_group.id)
        return self.get(request, ad_group.id)


class AdGroupSourcesRTBSerializer(serializers.Serializer):
    groupEnabled = serializers.BooleanField(source='b1_sources_group_enabled')
    dailyBudget = serializers.DecimalField(max_digits=10, decimal_places=4, source='b1_sources_group_daily_budget')
    state = DashConstantField(constants.AdGroupSourceSettingsState, source='b1_sources_group_state')

    def update(self, data_internal, validated_data):
        request = validated_data['request']
        del validated_data['request']
        settings = data_internal
        entity_id = int(settings['id'])
        settings.update(validated_data)
        request.body = RESTAPIJSONRenderer().render(({'settings': settings}))
        data_internal_new, _ = agency.AdGroupSettings(rest_proxy=True).put(request, entity_id)
        return data_internal_new['data']['settings']


class AdGroupSourcesRTBViewDetails(RESTAPIBaseView):

    def get(self, request, ad_group_id):
        view_internal = agency.AdGroupSettings(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, ad_group_id)
        serializer = AdGroupSourcesRTBSerializer(data_internal['data']['settings'])
        return self.response_ok(serializer.data, status=status_code)

    def put(self, request, ad_group_id):
        view_internal = agency.AdGroupSettings(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, ad_group_id)
        serializer = AdGroupSourcesRTBSerializer(data_internal['data']['settings'], request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)
        return self.response_ok(serializer.data, status=201)


class ContentAdSerializer(serializers.ModelSerializer):
    class Meta:
        model = dash.models.ContentAd
        fields = ('id', 'ad_group_id', 'state', 'url', 'title', 'image_url', 'display_url', 'brand_name',
                  'description', 'call_to_action', 'label', 'image_crop', 'tracker_urls')
        read_only_fields = tuple(set(fields) - set(('state',)))

    id = IdField()
    ad_group_id = IdField(source='ad_group')
    state = DashConstantField(constants.ContentAdSourceState)
    image_url = serializers.URLField(source='get_image_url')

    def create(self, validated_data):
        request = validated_data['request']
        content_ad_id = validated_data['content_ad_id']
        content_ad = dash.models.ContentAd.objects.get(pk=content_ad_id)
        post_data = {
            'state': validated_data['state'],
            'selected_ids': [int(content_ad_id)]
        }
        request.body = RESTAPIJSONRenderer().render(post_data)
        view_internal = views.AdGroupContentAdState(rest_proxy=True)
        data_internal, status_code = view_internal.post(request, content_ad.ad_group_id)
        content_ad.refresh_from_db()
        return content_ad


class ContentAdViewList(RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)

    def get(self, request):
        ad_group_id = request.query_params.get('adGroupId')
        if not ad_group_id:
            raise serializers.ValidationError('Must pass adGroupId parameter')
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content_ads = dash.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived()
        serializer = ContentAdSerializer(content_ads, many=True)
        return self.response_ok(serializer.data)


class ContentAdViewDetails(RESTAPIBaseView):

    def put(self, request, content_ad_id):
        serializer = ContentAdSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request, content_ad_id=content_ad_id)
        return self.response_ok(serializer.data)


class ContentAdCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = dash.models.ContentAdCandidate
        fields = ('url', 'title', 'image_url', 'display_url', 'brand_name',
                  'description', 'call_to_action', 'label', 'image_crop')
        extra_kwargs = {'primary_tracker_url': {'allow_empty': True}, 'secondary_tracker_url': {'allow_empty': True}}

    def to_internal_value(self, external_data):
        internal_data = super(ContentAdCandidateSerializer, self).to_internal_value(external_data)
        tracker_urls = external_data.get('tracker_urls')
        if not tracker_urls:
            return internal_data
        if len(tracker_urls) > 0:
            internal_data['primary_tracker_url'] = tracker_urls[0]
        if len(tracker_urls) > 1:
            internal_data['secondary_tracker_url'] = tracker_urls[1]
        if len(tracker_urls) > 2:
            raise serializers.ValidationError('A maximum of two tracker URLs are supported.')
        return internal_data


class UploadBatchSerializer(serializers.Serializer):
    id = IdField()
    status = DashConstantField(constants.UploadBatchStatus)
    approvedContentAds = ContentAdSerializer(many=True, source='get_approved_content_ads')

    def to_representation(self, batch):
        external_data = super(UploadBatchSerializer, self).to_representation(batch)
        cleaned_candidates = upload.get_candidates_with_errors(batch.contentadcandidate_set.all())
        external_data['validationStatus'] = [candidate['errors'] for candidate in cleaned_candidates]
        return external_data


class ContentAdBatchViewList(RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)
    parser_classes = (CamelCaseJSONParser,)

    def post(self, request):
        ad_group_id = request.query_params.get('adGroupId')
        if not ad_group_id:
            raise serializers.ValidationError('Must pass adGroupId parameter')
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        serializer = ContentAdCandidateSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        batch_name = self._generate_batch_name('API Upload')
        candidates_data = serializer.validated_data
        filename = None

        batch, candidates = upload.insert_candidates(
            candidates_data,
            ad_group,
            batch_name,
            filename,
            auto_save=True,
        )

        batch_serializer = UploadBatchSerializer(batch)
        return self.response_ok(batch_serializer.data, status=201)

    @staticmethod
    def _generate_batch_name(prefix):
        return '%s %s' % (prefix, dates_helper.local_now().strftime('M/D/YYYY h:mm A'))


class ContentAdBatchViewDetails(RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)

    def get(self, request, batch_id):
        try:
            batch = dash.models.UploadBatch.objects.get(id=batch_id)
        except dash.models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')
        helpers.get_ad_group(request.user, batch.ad_group_id)  # permissions check

        batch_serializer = UploadBatchSerializer(batch)
        return self.response_ok(batch_serializer.data)


class ReportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = restapi.models.ReportJob
        fields = ('id', 'status', 'result')
    id = IdField()
    status = DashConstantField(constants.ReportJobStatus)
    result = serializers.JSONField()


class ReportsViewList(RESTAPIBaseView):

    def post(self, request):
        query = restapi.reports.ReportQuerySerializer(data=request.data)
        query.is_valid(raise_exception=True)

        job = restapi.models.ReportJob(user=request.user, query=query.data)
        job.save()

        executor = restapi.reports.ReportJobExecutor(job)
        thread = dash.threads.AsyncFunction(executor.execute)
        thread.start()

        return self.response_ok(ReportJobSerializer(job).data, status=201)


class ReportsViewDetails(RESTAPIBaseView):

    def get(self, request, job_id):
        job = restapi.models.ReportJob.objects.get(pk=job_id)
        return self.response_ok(ReportJobSerializer(job).data)
