from rest_framework import serializers

import dash.constants
import dash.views.helpers
from restapi.fields import IdField, DashConstantField
import stats.api_reports
import stats.constants
from utils import exc

import constants
import helpers
import models


class ReportNamesSerializer(serializers.Serializer):
    field = serializers.CharField(allow_blank=False, trim_whitespace=True)


class ReportFiltersSerializer(serializers.Serializer):
    field = serializers.CharField(allow_blank=False, trim_whitespace=True)
    operator = serializers.ChoiceField(constants.OPERATORS)
    value = serializers.CharField(required=False)
    values = serializers.ListField(child=serializers.CharField(), required=False)
    frm = serializers.CharField(required=False)  # remapped to 'from' below
    to = serializers.CharField(required=False)


# from is a reserved keyword, remap it directly
ReportFiltersSerializer._declared_fields['from'] = ReportFiltersSerializer._declared_fields['frm']
del ReportFiltersSerializer._declared_fields['frm']


class ReportOptionsSerializer(serializers.Serializer):
    show_archived = serializers.BooleanField(default=False)
    show_blacklisted_publishers = serializers.ChoiceField(
        dash.constants.PublisherBlacklistFilter.get_all(), default=dash.constants.PublisherBlacklistFilter.SHOW_ALL)
    include_totals = serializers.BooleanField(default=False)
    include_items_with_no_spend = serializers.BooleanField(default=False)
    show_status_date = serializers.BooleanField(default=False)
    recipients = serializers.ListField(child=serializers.EmailField(), default=[])
    order = serializers.CharField(required=False)


class ReportQuerySerializer(serializers.Serializer):
    fields = ReportNamesSerializer(many=True)
    filters = ReportFiltersSerializer(many=True)
    options = ReportOptionsSerializer(default={})

    def validate_filters(self, filters):
        filter_constraints = helpers.get_filter_constraints(filters)
        if 'start_date' not in filter_constraints or 'end_date' not in filter_constraints:
            raise serializers.ValidationError("Please specify a date range!")
        if 'ad_group_id' in filter_constraints:
            dash.views.helpers.get_ad_group(self.context['request'].user, filter_constraints['ad_group_id'])
        if 'campaign_id' in filter_constraints:
            dash.views.helpers.get_campaign(self.context['request'].user, filter_constraints['campaign_id'])
        if 'account_id' in filter_constraints:
            dash.views.helpers.get_account(self.context['request'].user, filter_constraints['account_id'])
        return filters

    def validate(self, data):
        filter_constraints = helpers.get_filter_constraints(data['filters'])
        level = helpers.get_level_from_constraints(filter_constraints)
        breakdown = helpers.get_breakdown_from_fields(data['fields'], level)
        try:
            stats.api_reports.validate_breakdown_by_structure(level, breakdown)
            stats.api_reports.validate_breakdown_by_permissions(level, self.context['request'].user, breakdown)
        except exc.InvalidBreakdownError as e:
            raise serializers.ValidationError(e)
        if stats.constants.get_delivery_dimension(breakdown):
            raise serializers.ValidationError("Delivery dimension not supported!")
        return data


class ReportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReportJob
        fields = ('id', 'status', 'result')
    id = IdField()
    status = DashConstantField(constants.ReportJobStatus)
    result = serializers.JSONField()
