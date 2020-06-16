import rest_framework.serializers

import dash.constants
import restapi.serializers.base
import restapi.serializers.fields


class AlertQueryParams(restapi.serializers.serializers.QueryParamsExpectations):
    breakdown = rest_framework.serializers.CharField(required=False, allow_null=True)
    start_date = rest_framework.serializers.DateField(required=False, allow_null=True)
    end_date = rest_framework.serializers.DateField(required=False, allow_null=True)


class AlertSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(dash.constants.AlertType, read_only=True)
    message = rest_framework.serializers.CharField(read_only=True)
    is_closable = rest_framework.serializers.BooleanField(default=False, read_only=True)
