from rest_framework import serializers

import restapi.serializers.fields
import stats.constants
import zemauth.access
from dash import constants
from dash.features.reports import helpers as reports_helpers
from dash.features.reports import serializers as reports_serializers
from zemauth.features.entity_permission import Permission


class ScheduledReportSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    name = restapi.serializers.fields.PlainCharField(max_length=100)
    user = serializers.SerializerMethodField()

    query = reports_serializers.ReportQuerySerializer(write_only=True)

    frequency = restapi.serializers.fields.DashConstantField(
        constants.ScheduledReportSendingFrequency, source="sending_frequency"
    )
    day_of_week = restapi.serializers.fields.DashConstantField(constants.ScheduledReportDayOfWeek)
    time_period = restapi.serializers.fields.DashConstantField(constants.ScheduledReportTimePeriod)

    level = serializers.SerializerMethodField()
    breakdown = serializers.SerializerMethodField()
    recipients = serializers.ListField(read_only=True, source="get_recipients")

    def get_level(self, obj):
        constraints = reports_helpers.get_filter_constraints(obj.query["filters"])
        if stats.constants.AD_GROUP in constraints:
            ad_group = zemauth.access.get_ad_group(obj.user, Permission.READ, constraints[stats.constants.AD_GROUP])
            return "Ad Group - " + ad_group.name
        elif stats.constants.CAMPAIGN in constraints:
            campaign = zemauth.access.get_campaign(obj.user, Permission.READ, constraints[stats.constants.CAMPAIGN])
            return "Campaign - " + campaign.name
        elif stats.constants.ACCOUNT in constraints:
            account = zemauth.access.get_account(obj.user, Permission.READ, constraints[stats.constants.ACCOUNT])
            return "Account - " + account.name
        else:
            return "All accounts"

    def get_breakdown(self, obj):
        return ["By " + breakdown for breakdown in reports_helpers.get_breakdown_names(obj.query)]

    def validate_query(self, query):
        if len(query["options"]["recipients"]) <= 0:
            raise serializers.ValidationError({"options": {"recipients": ["Please enter at least one recipient"]}})
        return query

    def get_user(self, obj):
        if not obj.user:
            return ""

        full_name = obj.user.get_full_name().strip()
        if not full_name:
            return "{}".format(obj.user.email)

        return "{} ({})".format(full_name, obj.user.email)
