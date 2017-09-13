import collections
import logging
import influx
import ipware.ip
import time
import json

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
import rest_framework.renderers
import rest_framework.parsers
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import pagination
from rest_framework import exceptions
from djangorestframework_camel_case.parser import CamelCaseJSONParser
import djangorestframework_camel_case.util

from utils import json_helper, exc, dates_helper

from dash.views import agency, bulk_actions, views, helpers
from dash import campaign_goals
from dash import constants
from dash.features.reports import reportjob
from dash.features.reports import serializers as reports_serializers
from dash.features.reports import reports
import dash.models
from dash.features import contentupload
import redshiftapi.quickstats

import utils.rest_common.authentication
import fields
import bcm.views
import core.bcm

import dash.features.geolocation

logger = logging.getLogger(__name__)


class RESTAPIJSONRenderer(rest_framework.renderers.JSONRenderer):
    encoder_class = json_helper.JSONEncoder

    def render(self, data, *args, **kwargs):
        return super(RESTAPIJSONRenderer, self).render(
            djangorestframework_camel_case.util.camelize(data), *args, **kwargs
        )


class CanUseRESTAPIPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_use_restapi'))


class RESTAPIBaseView(APIView):
    authentication_classes = [
        utils.rest_common.authentication.OAuth2Authentication,
        utils.rest_common.authentication.SessionAuthentication,
    ]

    renderer_classes = [RESTAPIJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = (permissions.IsAuthenticated, CanUseRESTAPIPermission,)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def initialize_request(self, request, *args, **kwargs):
        drf_request = super(RESTAPIBaseView, self).initialize_request(request, *args, **kwargs)
        drf_request.method = request.method
        drf_request.start_time = time.time()
        return drf_request

    def finalize_response(self, request, response, *args, **kwargs):
        drf_response = super(RESTAPIBaseView, self).finalize_response(request, response, *args, **kwargs)
        user = getattr(request, 'user', None)
        user_email = getattr(user, 'email', 'unknown')
        influx.timing(
            'restapi.request',
            (time.time() - request.start_time),
            endpoint=self.__class__.__name__,
            method=request.method,
            status=str(response.status_code),
            user=user_email
        )
        logger.debug('REST API request/response: endpoint={endpoint}, method={method}, status={status}, user={user}, ip={ip}'.format(
            endpoint=self.__class__.__name__,
            method=request.method,
            status=str(response.status_code),
            user=user_email,
            ip=ipware.ip.get_ip(request)
        ))
        return drf_response

    @staticmethod
    def response_ok(data, errors=None, **kwargs):
        data = {'data': data}
        if errors:
            data['errors'] = errors
        return Response(data, **kwargs)


class RESTAPIBaseViewSet(ViewSetMixin, RESTAPIBaseView):
    pass


class DataNodeSerializerMixin(object):

    @property
    def data(self):
        return {
            'data': super(DataNodeSerializerMixin, self).data,
        }


class DataNodeListSerializer(DataNodeSerializerMixin, serializers.ListSerializer):
    pass


class StandardPagination(pagination.LimitOffsetPagination):
    max_limit = 1000
    default_limit = 100

    def get_paginated_response(self, data):
        if 'data' in data:
            data = data['data']

        return Response(collections.OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ]))


class SettingsSerializer(serializers.BaseSerializer):

    def __init__(self, request, view_internal, *args, **kwargs):
        self.request = request
        self.view_internal = view_internal
        super(SettingsSerializer, self).__init__(*args, **kwargs)

    def update(self, data_internal, validated_data):
        if not validated_data['settings']:
            return data_internal
        settings = data_internal['data']['settings']
        entity_id = int(settings['id'])
        settings.update(validated_data['settings'])
        self.request.body = json.dumps(({'settings': settings}), cls=json_helper.JSONEncoder)
        data_internal_new, _ = self.view_internal.put(self.request, entity_id)
        return data_internal_new

    @classmethod
    def many_init(cls, request, view_internal, *args, **kwargs):
        kwargs['child'] = cls(request, view_internal, *args, **kwargs)
        return serializers.ListSerializer(*args, **kwargs)

    @classmethod
    def _allow_not_provided(cls, d):
        if d == fields.NOT_PROVIDED:
            return fields.NOT_PROVIDED
        new_dict = collections.defaultdict(lambda: fields.NOT_PROVIDED)
        new_dict.update(d)
        for key, value in new_dict.items():
            if isinstance(value, dict):
                new_dict[key] = cls._allow_not_provided(value)
        return new_dict


class AccountSerializer(SettingsSerializer):

    def update(self, data_internal, validated_data):
        data_internal_new = super(AccountSerializer, self).update(data_internal, validated_data)
        return data_internal_new

    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        return {
            'id': settings['id'],
            'name': settings['name'],
            'targeting': {
                'publisherGroups': {
                    'included': settings['whitelist_publisher_groups'],
                    'excluded': settings['blacklist_publisher_groups'],
                }
            }
        }

    def to_internal_value(self, external_data):
        data = self._allow_not_provided(external_data)
        settings = {
            'id': data['id'],
            'name': data['name'],
            'whitelist_publisher_groups': data['targeting']['publisherGroups']['included'],
            'blacklist_publisher_groups': data['targeting']['publisherGroups']['excluded'],
        }
        return {'settings': {k: v for k, v in settings.items() if v != fields.NOT_PROVIDED}}


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
        internal_view = bcm.views.AccountCreditView(rest_proxy=True)
        data_internal, _ = internal_view.get(self.request, account_id)
        serializer = AccountCreditSerializer(data_internal['data']['active'], many=True)
        return self.response_ok(serializer.data)


class CampaignSerializer(SettingsSerializer):

    def update(self, data_internal, validated_data):
        """ Handle archived update separately, since it's on a separate endpoint """
        id_ = data_internal['data']['settings']['id']

        old_archived = data_internal['data']['archived']
        new_archived = validated_data['settings'].get('archived')

        with transaction.atomic():
            data_internal_new = super(CampaignSerializer, self).update(data_internal, validated_data)

            if new_archived is not None and new_archived != old_archived:
                entity_id = int(id_)
                self.request.body = ''
                internal_view = views.CampaignArchive(
                    rest_proxy=True
                ) if new_archived else views.CampaignRestore(rest_proxy=True)
                data_internal_archived, _ = internal_view.post(self.request, entity_id)
                data_internal_new['data']['archived'] = new_archived

            return data_internal_new

    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        return {
            'id': settings['id'],
            'accountId': settings['account_id'],
            'name': settings['name'],
            'archived': data_internal['data']['archived'],
            'iabCategory': fields.DashConstantField(constants.IABCategory).to_representation(settings['iab_category']),
            # 'campaignManager': self._user_to_email(settings['campaign_manager']),  # TODO(nsaje): convert to email
            'tracking': {
                'ga': {
                    'enabled': settings['enable_ga_tracking'],
                    'type': fields.DashConstantField(constants.GATrackingType).to_representation(settings['ga_tracking_type']),
                    'webPropertyId': settings['ga_property_id'],
                },
                'adobe': {
                    'enabled': settings['enable_adobe_tracking'],
                    'trackingParameter': settings['adobe_tracking_param'],
                },
            },
            'targeting': {
                'devices': settings['target_devices'],
                'placements': settings['target_placements'],
                'os': settings['target_os'],
                'publisherGroups': {
                    'included': settings['whitelist_publisher_groups'],
                    'excluded': settings['blacklist_publisher_groups'],
                }
            }
        }

    def to_internal_value(self, external_data):
        data = self._allow_not_provided(external_data)
        settings = {
            'id': data['id'],
            'name': data['name'],
            'iab_category': fields.DashConstantField(constants.IABCategory).to_internal_value(data['iabCategory']),
            'archived': data['archived'],
            # 'campaign_manager': data['campaignManager'],  # TODO(nsaje): convert from email
            'enable_ga_tracking': data['tracking']['ga']['enabled'],
            'ga_tracking_type': fields.DashConstantField(constants.GATrackingType).to_internal_value(data['tracking']['ga']['type']),
            'ga_property_id': data['tracking']['ga']['webPropertyId'],
            'enable_adobe_tracking': data['tracking']['adobe']['enabled'],
            'adobe_tracking_param': data['tracking']['adobe']['trackingParameter'],
            'whitelist_publisher_groups': data['targeting']['publisherGroups']['included'],
            'blacklist_publisher_groups': data['targeting']['publisherGroups']['excluded'],

            # TODO (refactor-workaround) Deserialization done in Django View
            'target_devices': data['targeting']['devices'],
            'target_placements': data['targeting']['placements'],
            'target_os': data['targeting']['os'],
        }
        if (settings['iab_category'] != fields.NOT_PROVIDED and
                settings['iab_category'] != dash.constants.IABCategory.IAB24 and
                '-' not in settings['iab_category']):
            raise serializers.ValidationError(
                {'iabCategory': 'Tier 1 IAB categories not allowed, please use Tier 2 IAB categories.'})
        return {'settings': {k: v for k, v in settings.items() if v != fields.NOT_PROVIDED}}


class AdGroupSerializer(SettingsSerializer):

    def update(self, data_internal, validated_data):
        """ Handle state and archived update separately, since they're on separate endpoints """
        id_ = data_internal['data']['settings']['id']

        old_state = data_internal['data']['settings']['state']
        new_state = validated_data['settings'].get('state')

        old_archived = data_internal['data']['archived']
        new_archived = validated_data['settings'].get('archived')

        with transaction.atomic():
            data_internal_new = super(AdGroupSerializer, self).update(data_internal, validated_data)

            if new_state and new_state != old_state:
                entity_id = int(id_)
                self.request.body = json.dumps({'state': new_state}, cls=json_helper.JSONEncoder)
                internal_view = agency.AdGroupSettingsState(rest_proxy=True)
                data_internal_state, _ = internal_view.post(self.request, entity_id)
                data_internal_new['data'].update(data_internal_state['data'])

            if new_archived is not None and new_archived != old_archived:
                entity_id = int(id_)
                self.request.body = ''
                internal_view = views.AdGroupArchive(
                    rest_proxy=True) if new_archived else views.AdGroupRestore(rest_proxy=True)
                data_internal_archived, _ = internal_view.post(self.request, entity_id)
                data_internal_new['data']['archived'] = new_archived

            return data_internal_new

    def to_representation(self, data_internal):
        settings = data_internal['data']['settings']
        ret = {
            'id': settings['id'],
            'archived': data_internal['data']['archived'],
            'campaignId': settings['campaign_id'],
            'name': settings['name'],
            'state': constants.AdGroupSettingsState.get_name(settings['state']),
            'startDate': settings['start_date'],
            'endDate': settings['end_date'],
            'maxCpc': settings['cpc_cc'],
            'maxCpm': settings['max_cpm'],
            'dailyBudget': settings['daily_budget_cc'],
            'trackingCode': settings['tracking_code'],
            'targeting': {
                'geo': {
                    'included': settings['target_regions'],
                    'excluded': settings['exclusion_target_regions'],
                },
                'devices': settings['target_devices'],
                'os': settings['target_os'],
                'placements': settings['target_placements'],
                'interest': {
                    'included': map(lambda x: fields.DashConstantField(constants.InterestCategory).to_representation(x), settings['interest_targeting']),
                    'excluded': map(lambda x: fields.DashConstantField(constants.InterestCategory).to_representation(x), settings['exclusion_interest_targeting']),
                },
                'demographic': settings['bluekai_targeting_old'],
                'audience': settings['bluekai_targeting'],
                'publisherGroups': {
                    'included': settings['whitelist_publisher_groups'],
                    'excluded': settings['blacklist_publisher_groups'],
                },
                'customAudiences': {
                    'included': settings['audience_targeting'],
                    'excluded': settings['exclusion_audience_targeting'],
                },
                'retargetingAdGroups': {
                    'included': settings['retargeting_ad_groups'],
                    'excluded': settings['exclusion_retargeting_ad_groups'],
                }
            },
            'autopilot': {
                'state': constants.AdGroupSettingsAutopilotState.get_name(settings['autopilot_state']),
                'dailyBudget': settings['autopilot_daily_budget'],
            },
            'dayparting': settings['dayparting'],
            'deliveryType': constants.AdGroupDeliveryType.get_name(settings['delivery_type']),
        }
        if 'click_capping_daily_ad_group_max_clicks' in settings:
            ret['clickCappingDailyAdGroupMaxClicks'] = settings['click_capping_daily_ad_group_max_clicks']

        return ret

    def to_internal_value(self, external_data):
        data = self._allow_not_provided(external_data)
        settings = {
            'id': data['id'],
            'name': data['name'],
            'state': fields.DashConstantField(constants.AdGroupSettingsState).to_internal_value(data['state']),
            'archived': data['archived'],
            'start_date': data['startDate'],
            'end_date': data['endDate'],
            'cpc_cc': data['maxCpc'],
            'max_cpm': data['maxCpm'],
            'daily_budget_cc': data['dailyBudget'],
            'tracking_code': data['trackingCode'],
            'interest_targeting': fields.DashConstantField(constants.InterestCategory).to_internal_value_many(data['targeting']['interest']['included']),
            'exclusion_interest_targeting': fields.DashConstantField(constants.InterestCategory).to_internal_value_many(data['targeting']['interest']['excluded']),
            'bluekai_targeting': self._handle_audience_targeting(data),
            'autopilot_state': fields.DashConstantField(constants.AdGroupSettingsAutopilotState).to_internal_value(data['autopilot']['state']),
            'autopilot_daily_budget': data['autopilot']['dailyBudget'],
            'dayparting': data['dayparting'],
            'whitelist_publisher_groups': data['targeting']['publisherGroups']['included'],
            'blacklist_publisher_groups': data['targeting']['publisherGroups']['excluded'],
            'audience_targeting': data['targeting']['customAudiences']['included'],
            'exclusion_audience_targeting': data['targeting']['customAudiences']['excluded'],
            'retargeting_ad_groups': data['targeting']['retargetingAdGroups']['included'],
            'exclusion_retargeting_ad_groups': data['targeting']['retargetingAdGroups']['excluded'],

            # TODO (refactor-workaround) Deserialization done in Django Views
            'target_regions': data['targeting']['geo']['included'],
            'exclusion_target_regions': data['targeting']['geo']['excluded'],
            'target_devices': data['targeting']['devices'],
            'target_placements': data['targeting']['placements'],
            'target_os': data['targeting']['os'],
            'delivery_type': fields.DashConstantField(constants.AdGroupDeliveryType).to_internal_value(data['deliveryType']),
            'click_capping_daily_ad_group_max_clicks': data['clickCappingDailyAdGroupMaxClicks'],
        }
        return {'settings': {k: v for k, v in settings.items() if v != fields.NOT_PROVIDED}}

    @staticmethod
    def _partition_regions(target_regions):
        geo = {
            'countries': [],
            'regions': [],
            'dma': [],
            'cities': [],
            'postalCodes': [],
        }
        non_zips = {loc.key: loc for loc in dash.features.geolocation.Geolocation.objects.filter(
            key__in=target_regions)}
        zips = set(target_regions) - set(non_zips.keys())
        for location in target_regions:
            if location in non_zips:
                if non_zips[location].type == constants.LocationType.COUNTRY:
                    geo['countries'].append(location)
                if non_zips[location].type == constants.LocationType.REGION:
                    geo['regions'].append(location)
                if non_zips[location].type == constants.LocationType.DMA:
                    geo['dma'].append(location)
                if non_zips[location].type == constants.LocationType.CITY:
                    geo['cities'].append(location)
            if location in zips:
                geo['postalCodes'].append(location)
        return geo

    @staticmethod
    def _unpartition_regions(geo):
        if geo == fields.NOT_PROVIDED:
            return fields.NOT_PROVIDED
        target_regions = []
        target_regions.extend(geo['countries'])
        target_regions.extend(geo['regions'])
        target_regions.extend(geo['dma'])
        target_regions.extend(geo['cities'])
        target_regions.extend(geo['postalCodes'])
        return target_regions

    @staticmethod
    def _handle_audience_targeting(data):
        if data['targeting']['audience'] != fields.NOT_PROVIDED:
            return data['targeting']['audience']
        return data['targeting']['demographic']


class SettingsViewDetails(RESTAPIBaseView):

    parser_classes = (rest_framework.parsers.JSONParser,)

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
        return self.response_ok(serializer.data)


class SettingsViewList(RESTAPIBaseView):

    parser_classes = (rest_framework.parsers.JSONParser,)

    def _get_settings_list(self, request):
        raise NotImplementedError()

    def get(self, request):
        view_internal = self.internal_view_cls(rest_proxy=True)
        settings_list = self._get_settings_list(request)
        data_list_internal = [{'data': {
            'settings': view_internal.get_dict(
                request,
                settings,
                (getattr(settings, 'ad_group', None) or
                 getattr(settings, 'campaign', None) or
                 getattr(settings, 'account'))
            ),
            'archived': settings.archived
        }}
            for settings in settings_list]
        serializer = self.serializer_cls(request, view_internal, data_list_internal, many=True)
        return self.response_ok(serializer.data)

    def post(self, request):
        if not hasattr(self, 'internal_create_view_cls'):
            raise exceptions.MethodNotAllowed('POST')
        with transaction.atomic():
            create_view_internal = self.internal_create_view_cls(rest_proxy=True)
            parent_id = request.data.get(self.parent_id_field)
            if not parent_id:
                raise serializers.ValidationError({self.parent_id_field: 'required'})
            data_internal, status_code = create_view_internal.put(request, int(parent_id))
            entity_id = data_internal['data']['id']
            response = self.details_view_cls().put(request, entity_id)
            if response.status_code != 200:
                transaction.set_rollback(True)
            response.status_code = 201
            return response


class AccountViewDetails(SettingsViewDetails):
    internal_view_cls = agency.AccountSettings
    serializer_cls = AccountSerializer


class AccountViewList(SettingsViewList):
    internal_view_cls = agency.AccountSettings
    serializer_cls = AccountSerializer
    details_view_cls = AccountViewDetails

    def _get_settings_list(self, request):
        accounts = dash.models.Account.objects.all().filter_by_user(request.user)
        account_settings = dash.models.AccountSettings.objects.filter(
            account__in=accounts).group_current_settings().select_related('account')
        return account_settings


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

        if account_id:
            account = helpers.get_account(request.user, account_id)
            campaigns = dash.models.Campaign.objects.filter(account=account)
        else:
            campaigns = dash.models.Campaign.objects.all().filter_by_user(request.user)

        campaign_settings = dash.models.CampaignSettingsReadOnly.objects.filter(
            campaign__in=campaigns).group_current_settings().select_related('campaign', 'campaign_manager')

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

        if campaign_id:
            campaign = helpers.get_campaign(request.user, campaign_id)
            ad_groups = dash.models.AdGroup.objects.filter(campaign=campaign)
        else:
            ad_groups = dash.models.AdGroup.objects.all().filter_by_user(request.user)

        ag_settings = dash.models.AdGroupSettings.objects.filter(
            ad_group__in=ad_groups).group_current_settings().select_related('ad_group')
        return ag_settings


class CampaignGoalsSerializer(serializers.BaseSerializer):

    def to_representation(self, data_internal):
        return {
            'id': data_internal['id'],
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
            'conversionWindow': fields.DashConstantField(constants.ConversionWindows).to_representation(conversion_goal['conversion_window']),
            'type': constants.ConversionGoalType.get_name(conversion_goal['type']),
        }

    def to_internal_value(self, data_external):
        try:
            return {
                'primary': data_external['primary'],
                'type': fields.DashConstantField(constants.CampaignGoalKPI).to_internal_value(data_external['type']),
                'conversion_goal': self._conversion_goal_to_internal_value(data_external.get('conversionGoal')),
                'value': data_external['value']
            }
        except KeyError as e:
            raise serializers.ValidationError({e.message: 'missing'})

    def _conversion_goal_to_internal_value(self, conversion_goal):
        if not conversion_goal:
            return conversion_goal
        return {
            'goal_id': conversion_goal['goalId'],
            'conversion_window': fields.DashConstantField(constants.ConversionWindows).to_internal_value(conversion_goal['conversionWindow']),
            'type': fields.DashConstantField(constants.ConversionGoalType).to_internal_value(conversion_goal['type']),
        }


class CampaignGoalsViewList(RESTAPIBaseView):
    parser_classes = (rest_framework.parsers.JSONParser,)

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
        self.request.body = json.dumps(put_data, cls=json_helper.JSONEncoder)
        data_internal, status_code = view_internal.put(request, int(campaign_id))
        return self.response_ok(CampaignGoalsSerializer(data_internal['data']['goals'][-1]).data, status=201)


class CampaignGoalPutSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=15, decimal_places=5)
    primary = serializers.BooleanField()


class CampaignGoalsViewDetails(RESTAPIBaseView):
    parser_classes = (rest_framework.parsers.JSONParser,)

    def get(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        goal = dash.models.CampaignGoal.objects.get(pk=goal_id, campaign=campaign)
        return self.response_ok(CampaignGoalsSerializer(goal.to_dict(with_values=True)).data)

    def put(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        serializer = CampaignGoalPutSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id, campaign=campaign)
            value = serializer.validated_data.get('value', None)
            if value:
                goal.add_value(request, value)
            primary = serializer.validated_data.get('primary', None)
            if primary:
                goal.set_primary(request)
            goal.refresh_from_db()
            return self.response_ok(CampaignGoalsSerializer(goal.to_dict(with_values=True)).data)

    def delete(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        try:
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
        except dash.models.CampaignGoal.DoesNotExist:
            raise exc.MissingDataError('Goal does not exist')
        campaign_goals.delete_campaign_goal(request, goal.id, campaign)
        return Response(None, status=204)


class CampaignBudgetSerializer(serializers.Serializer):
    id = fields.IdField(read_only=True)
    credit_id = fields.IdField(source='credit')
    amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    state = fields.DashConstantField(constants.BudgetLineItemState, read_only=True)
    spend = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    available = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)


class CampaignBudgetViewList(RESTAPIBaseView):

    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        active_budget = self._get_active_budget(request.user, campaign)
        serializer = CampaignBudgetSerializer(active_budget, many=True)
        return self.response_ok(serializer.data)

    def _get_active_budget(self, user, campaign):
        budget_items = core.bcm.BudgetLineItem.objects.filter(
            campaign_id=campaign.id,
        ).select_related('credit', 'campaign__account').order_by('-created_dt')

        return [self._prepare_budget_get_item(user, b) for b in budget_items if b.state() in (
            constants.BudgetLineItemState.ACTIVE,
            constants.BudgetLineItemState.PENDING,
        )]

    def _prepare_budget_get_item(self, user, item):
        if item.campaign.account.uses_bcm_v2:
            spend = item.get_spend_data()['etfm_total']
        else:
            spend = item.get_spend_data()['etf_total']

        allocated = item.allocated_amount()
        result = {
            'id': item.pk,
            'start_date': item.start_date,
            'credit': item.credit_id,
            'end_date': item.end_date,
            'state': item.state(),
            'amount': allocated,
            'spend': spend,
            'available': allocated - spend,
        }
        return result

    def post(self, request, campaign_id):
        serializer = CampaignBudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        internal_view = bcm.views.CampaignBudgetView(rest_proxy=True)
        post_data = serializer.validated_data

        self.request.body = json.dumps(post_data, cls=json_helper.JSONEncoder)
        data_internal, _ = internal_view.put(self.request, campaign_id)
        budget_id = int(data_internal['data'])
        response = CampaignBudgetViewDetails().get(self.request, campaign_id, budget_id)
        if response.status_code == 200:
            response.status_code = 201
        return response


class CampaignBudgetViewDetails(RESTAPIBaseView):

    def get(self, request, campaign_id, budget_id):
        internal_view = bcm.views.CampaignBudgetItemView(rest_proxy=True)
        data_internal, _ = internal_view.get(request, campaign_id, budget_id)
        data_internal['data']['credit'] = data_internal['data']['credit']['id']
        serializer = CampaignBudgetSerializer(data_internal['data'])
        return self.response_ok(serializer.data)

    def put(self, request, campaign_id, budget_id):
        internal_view = bcm.views.CampaignBudgetItemView(rest_proxy=True)

        data_internal_get, _ = internal_view.get(request, campaign_id, budget_id)
        serializer = CampaignBudgetSerializer(instance=data_internal_get['data'], data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        put_data = {k: data_internal_get['data'][k] for k in ['credit', 'amount', 'start_date', 'end_date', 'comment']}
        put_data['credit'] = put_data['credit']['id']
        put_data.update(serializer.validated_data)
        self.request.body = json.dumps(put_data, cls=json_helper.JSONEncoder)
        internal_view.post(self.request, campaign_id, budget_id)
        return CampaignBudgetViewDetails().get(self.request, campaign_id, budget_id)


class StatsSerializer(serializers.Serializer):
    total_cost = serializers.DecimalField(20, 2)
    impressions = serializers.IntegerField()
    clicks = serializers.IntegerField()
    cpc = serializers.DecimalField(5, 3)


class CampaignStatsView(RESTAPIBaseView):

    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        from_date = self.request.query_params.get('from', None)
        to_date = self.request.query_params.get('to', None)
        if not from_date or not to_date:
            raise serializers.ValidationError('Missing from or to parameter')
        stats = redshiftapi.quickstats.query_campaign(campaign.id, from_date, to_date)
        return self.response_ok(StatsSerializer(stats).data)


class AdGroupSourcesRTBSerializer(serializers.Serializer):
    group_enabled = serializers.BooleanField(source='b1_sources_group_enabled')
    daily_budget = serializers.DecimalField(max_digits=10, decimal_places=2, source='b1_sources_group_daily_budget')
    state = fields.DashConstantField(constants.AdGroupSourceSettingsState, source='b1_sources_group_state')
    cpc = serializers.DecimalField(max_digits=10, decimal_places=4, source='b1_sources_group_cpc_cc')

    def update(self, data_internal, validated_data):
        request = validated_data['request']
        del validated_data['request']
        settings = data_internal
        entity_id = int(settings['id'])
        settings.update(validated_data)
        request.body = json.dumps({'settings': settings}, cls=json_helper.JSONEncoder)
        data_internal_new, _ = agency.AdGroupSettings(rest_proxy=True).put(request, entity_id)
        return data_internal_new['data']['settings']


class AdGroupSourcesRTBViewDetails(RESTAPIBaseView):

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        settings = ad_group.get_current_settings()

        view_internal = agency.AdGroupSettings(rest_proxy=True)
        settings_dict = view_internal.get_dict(request, settings, ad_group)

        serializer = AdGroupSourcesRTBSerializer(settings_dict)
        return self.response_ok(serializer.data)

    def put(self, request, ad_group_id):
        view_internal = agency.AdGroupSettings(rest_proxy=True)
        data_internal, status_code = view_internal.get(request, ad_group_id)
        serializer = AdGroupSourcesRTBSerializer(data_internal['data']['settings'], request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)
        return self.response_ok(serializer.data)


class ContentAdSerializer(serializers.ModelSerializer):

    class Meta:
        model = dash.models.ContentAd
        fields = ('id', 'ad_group_id', 'state', 'url', 'title', 'image_url', 'display_url', 'brand_name',
                  'description', 'call_to_action', 'label', 'image_crop', 'tracker_urls')
        read_only_fields = tuple(set(fields) - set(('state',)))

    id = fields.IdField(required=False)
    ad_group_id = fields.IdField(source='ad_group', required=False)
    state = fields.DashConstantField(constants.ContentAdSourceState, required=True)
    image_url = serializers.URLField(source='get_image_url', required=False)

    def create(self, validated_data):
        request = validated_data['request']
        content_ad_id = validated_data['content_ad_id']
        content_ad = dash.models.ContentAd.objects.get(pk=content_ad_id)
        post_data = {
            'state': validated_data['state'],
            'selected_ids': [int(content_ad_id)]
        }
        request.body = json.dumps(post_data, cls=json_helper.JSONEncoder)
        view_internal = bulk_actions.AdGroupContentAdState(rest_proxy=True)
        data_internal, status_code = view_internal.post(request, content_ad.ad_group_id)
        content_ad.refresh_from_db()
        return content_ad


class ContentAdViewList(RESTAPIBaseView):

    def get(self, request):
        ad_group_id = request.query_params.get('adGroupId')
        if not ad_group_id:
            raise serializers.ValidationError('Must pass adGroupId parameter')
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content_ads = dash.models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived().select_related('ad_group')
        serializer = ContentAdSerializer(content_ads, many=True)
        return self.response_ok(serializer.data)


class ContentAdViewDetails(RESTAPIBaseView):

    def get(self, request, content_ad_id):
        content_ad = helpers.get_content_ad(request.user, content_ad_id)
        serializer = ContentAdSerializer(content_ad)
        return self.response_ok(serializer.data)

    def put(self, request, content_ad_id):
        helpers.get_content_ad(request.user, content_ad_id)  # validation
        serializer = ContentAdSerializer(data=request.data)
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
    id = fields.IdField()
    status = fields.DashConstantField(constants.UploadBatchStatus)
    approvedContentAds = ContentAdSerializer(many=True, source='get_approved_content_ads')

    def to_representation(self, batch):
        external_data = super(UploadBatchSerializer, self).to_representation(batch)
        cleaned_candidates = contentupload.upload.get_candidates_with_errors(batch.contentadcandidate_set.all())
        external_data['validationStatus'] = [candidate['errors'] for candidate in cleaned_candidates]
        return external_data


class ContentAdBatchViewList(RESTAPIBaseView):

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

        batch, candidates = contentupload.upload.insert_candidates(
            request.user,
            ad_group.campaign.account,
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
        return '%s %s' % (prefix, dates_helper.local_now().strftime('%m/%d/%Y %H:%M %z'))


class ContentAdBatchViewDetails(RESTAPIBaseView):

    def get(self, request, batch_id):
        try:
            batch = dash.models.UploadBatch.objects.get(id=batch_id)
        except dash.models.UploadBatch.DoesNotExist:
            raise exc.MissingDataError('Upload batch does not exist')
        helpers.get_ad_group(request.user, batch.ad_group_id)  # permissions check

        batch_serializer = UploadBatchSerializer(batch)
        return self.response_ok(batch_serializer.data)


class ReportsViewList(RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        query = reports_serializers.ReportQuerySerializer(data=request.data, context={'request': request})
        try:
            query.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.debug(e)
            raise e

        job = reports.create_job(request.user, query.data)

        return self.response_ok(reports_serializers.ReportJobSerializer(job).data, status=201)


class ReportsViewDetails(RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, job_id):
        job = reportjob.ReportJob.objects.get(pk=job_id)
        if job.user != request.user:
            raise exceptions.PermissionDenied
        return self.response_ok(reports_serializers.ReportJobSerializer(job).data)


class PublisherGroupSerializer(DataNodeSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = dash.models.PublisherGroup
        fields = ('id', 'name', 'account_id')
        list_serializer_class = DataNodeListSerializer

    id = fields.IdField(read_only=True)
    account_id = fields.IdField(read_only=True)

    def create(self, validated_data):
        pgroup = dash.models.PublisherGroup(
            name=validated_data['name'],
            account_id=validated_data['account_id'])
        pgroup.save(validated_data['request'])
        return pgroup

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save(validated_data['request'])
        return instance


class PublisherGroupEntrySerializer(DataNodeSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = dash.models.PublisherGroupEntry
        fields = ('id', 'publisher', 'publisher_group_id', 'source', 'include_subdomains')
        list_serializer_class = DataNodeListSerializer

    id = fields.IdField(read_only=True)
    publisher_group_id = fields.IdField(read_only=True)
    source = fields.SourceIdSlugField(required=False, allow_null=True)


class OutbrainPublisherGroupEntrySerializer(PublisherGroupEntrySerializer):

    class Meta:
        model = dash.models.PublisherGroupEntry
        fields = ('id', 'publisher', 'publisher_group_id', 'source', 'include_subdomains',
                  'outbrain_publisher_id', 'outbrain_section_id', 'outbrain_amplify_publisher_id', 'outbrain_engage_publisher_id')
        list_serializer_class = DataNodeListSerializer


class CanEditPublisherGroupsPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_edit_publisher_groups'))


class PublisherGroupViewSet(RESTAPIBaseView, viewsets.ModelViewSet):
    serializer_class = PublisherGroupSerializer
    lookup_url_kwarg = 'publisher_group_id'
    permission_classes = RESTAPIBaseView.permission_classes + (CanEditPublisherGroupsPermission,)

    def get_queryset(self):
        account = helpers.get_account(self.request.user, self.kwargs['account_id'])  # check user has account access
        return dash.models.PublisherGroup.objects.all().filter_by_account(account)

    def perform_create(self, serializer):
        helpers.get_account(self.request.user, self.kwargs['account_id'])
        serializer.save(request=self.request, account_id=self.kwargs['account_id'])

    def perform_update(self, serializer):
        serializer.save(request=self.request, account_id=self.kwargs['account_id'])

    def destroy(self, request, *args, **kwargs):
        publisher_group = self.get_object()
        if not publisher_group.can_delete():
            raise exc.ValidationError('This publisher group can not be deleted')

        return super(PublisherGroupViewSet, self).destroy(request, *args, **kwargs)


class PublisherGroupEntryViewSet(RESTAPIBaseView, viewsets.ModelViewSet):
    pagination_class = StandardPagination
    permission_classes = RESTAPIBaseView.permission_classes + (CanEditPublisherGroupsPermission,)

    lookup_url_kwarg = 'entry_id'

    def get_serializer_class(self):
        if self.request.user.has_perm('zemauth.can_access_additional_outbrain_publisher_settings'):
            return OutbrainPublisherGroupEntrySerializer
        return PublisherGroupEntrySerializer

    def get_queryset(self):
        publisher_group = dash.models.PublisherGroup.objects.get(pk=self.kwargs['publisher_group_id'])
        helpers.get_account(self.request.user, publisher_group.account_id)
        return publisher_group.entries.all()

    def create(self, request, *args, **kwargs):
        # support create multiple through the "many" parameter
        serializer = self.get_serializer(data=request.data, many=not isinstance(request.data, dict))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        publisher_group = dash.models.PublisherGroup.objects.get(pk=self.kwargs['publisher_group_id'])
        helpers.get_account(self.request.user, publisher_group.account_id)
        serializer.save(publisher_group_id=self.kwargs['publisher_group_id'])
