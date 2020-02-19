import rest_framework.serializers

import dash.constants
import restapi.serializers.base
import restapi.serializers.fields


class AudienceRulesSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(
        dash.constants.AudienceRuleType, error_messages={"required": "Please select the type of the rule."}
    )
    value = restapi.serializers.fields.PlainCharField(required=False, max_length=255, allow_blank=True)


class AudienceSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    pixel_id = restapi.serializers.fields.IdField(error_messages={"required": "Please select a pixel."})
    name = restapi.serializers.fields.PlainCharField(
        max_length=127, error_messages={"required": "Please specify the audience name."}
    )
    archived = rest_framework.serializers.BooleanField(required=False)
    ttl = rest_framework.serializers.IntegerField(
        max_value=365,
        error_messages={
            "required": "Please specify the user retention in days.",
            "max_value": "Maximum number of days is 365.",
        },
    )
    rules = AudienceRulesSerializer(
        source="audiencerule_set", error_messages={"required": "Please select a rule."}, many=True
    )
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
