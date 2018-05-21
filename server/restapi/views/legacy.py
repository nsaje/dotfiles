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

from utils import json_helper, exc

from dash.views import agency, helpers
from dash import campaign_goals
from dash import constants
from dash.features.reports import reportjob
from dash.features.reports import serializers as reports_serializers
from dash.features.reports import reports
import dash.models
import redshiftapi.api_quickstats

import utils.rest_common.authentication
from restapi import fields

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
        for key, value in list(new_dict.items()):
            if isinstance(value, dict):
                new_dict[key] = cls._allow_not_provided(value)
        return new_dict


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

    def _get_entities_list(self, request):
        raise NotImplementedError()

    def get(self, request):
        view_internal = self.internal_view_cls(rest_proxy=True)

        paginator = StandardPagination()
        paginator.default_limit = 50000  # FIXME(nsaje): remove this after OEN starts using pagination
        entities_list = self._get_entities_list(request).order_by('pk')
        entities_list_paginated = paginator.paginate_queryset(entities_list, request)

        data_list_internal = [{'data': {
            'settings': view_internal.get_dict(
                request,
                entity.settings,
                entity,
            ),
            'archived': entity.settings.archived
        }}
            for entity in entities_list_paginated]

        serializer = self.serializer_cls(request, view_internal, data_list_internal, many=True)
        return paginator.get_paginated_response(serializer.data)

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
            raise serializers.ValidationError({str(e): 'missing'})

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
        return self.response_ok(
            CampaignGoalsSerializer(goal.to_dict(with_values=True, local_values=True)).data
        )

    def put(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        serializer = CampaignGoalPutSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id, campaign=campaign)
            value = serializer.validated_data.get('value', None)
            if value:
                goal.add_local_value(request, value)
            primary = serializer.validated_data.get('primary', None)
            if primary:
                goal.set_primary(request)
            goal.refresh_from_db()
            return self.response_ok(
                CampaignGoalsSerializer(goal.to_dict(with_values=True, local_values=True)).data
            )

    def delete(self, request, campaign_id, goal_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        try:
            goal = dash.models.CampaignGoal.objects.get(pk=goal_id)
        except dash.models.CampaignGoal.DoesNotExist:
            raise exc.MissingDataError('Goal does not exist')
        campaign_goals.delete_campaign_goal(request, goal.id, campaign)
        return Response(None, status=204)


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
        stats = redshiftapi.api_quickstats.query_campaign(campaign.id, from_date, to_date)
        return self.response_ok(StatsSerializer(stats).data)


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
    name = fields.PlainCharField(max_length=127)
    account_id = fields.IdField(read_only=True)

    def create(self, validated_data):
        return dash.models.PublisherGroup.objects.create(
            validated_data['request'],
            name=validated_data['name'],
            account=helpers.get_account(validated_data['request'].user, validated_data['account_id']),
        )

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
    publisher = fields.PlainCharField(label='Publisher name or domain', max_length=127)
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
        return publisher_group.entries.all().select_related('source')

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
