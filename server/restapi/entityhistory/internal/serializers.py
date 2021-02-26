from datetime import datetime

import rest_framework.serializers

import dash.constants
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
from utils.dates_helper import utc_to_local

from . import constants


class EntityHistorySerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    datetime = rest_framework.serializers.DateTimeField(read_only=True, source="created_dt")
    changed_by = restapi.serializers.fields.PlainCharField(read_only=True, source="get_changed_by_text")
    changes_text = restapi.serializers.fields.PlainCharField(read_only=True)

    # TODO (jholas): remove when general solution is implemented
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["datetime"] = utc_to_local(datetime.fromisoformat(ret["datetime"]))
        return ret


class EntityHistoryQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    ad_group_id = restapi.serializers.fields.IdField(required=False)
    campaign_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    agency_id = restapi.serializers.fields.IdField(required=False)
    level = restapi.serializers.fields.DashConstantField(dash.constants.HistoryLevel)
    order = restapi.serializers.fields.DashConstantField(constants.EntityHistoryOrder, required=False)
    from_date = rest_framework.serializers.DateField(required=False)

    def validate(self, data):
        valid_entities = ["ad_group_id", "campaign_id", "account_id", "agency_id"]
        if not set(data.keys()).intersection(set(valid_entities)):
            raise rest_framework.serializers.ValidationError(
                "Either {} or {} must be provided.".format(", ".join(valid_entities[:-1]), valid_entities[-1])
            )
        return data
