import decimal

from rest_framework import serializers

import dash.models
import restapi.serializers.fields
from dash import constants


class AdGroupSourceListSerializer(serializers.ListSerializer):
    def to_internal_value(self, data):

        if not isinstance(data, list):
            # Data should only be processed if it is a list; if not, validation will fail in super call.
            return super().to_internal_value(data)

        source_slugs = []
        for item in data:
            source = item.get("source", None)
            if not source:
                raise serializers.ValidationError("Object '%s' has no source!" % item)

            source_slugs.append(source)
        sources = dash.models.Source.objects.filter(bidder_slug__in=source_slugs)
        sources_by_slug = {s.bidder_slug: s for s in sources}
        for item in data:
            source = sources_by_slug.get(item.get("source"), None)
            if not source:
                raise serializers.ValidationError("Invalid source in object '%s'!" % item)
            item["source"] = source

        ret = super().to_internal_value(data)
        return ret


class AdGroupSourceSerializer(restapi.serializers.serializers.PermissionedFieldsMixin, serializers.Serializer):
    class Meta:
        list_serializer_class = AdGroupSourceListSerializer
        permissioned_fields = {}

    @property
    def fields(self):
        fields = super().fields
        ad_group = self.context.get("ad_group")
        if ad_group and ad_group.bidding_type == constants.BiddingType.CPM:
            fields["cpc"].allow_null = True
        elif "cpm" in fields:
            fields["cpm"].allow_null = True
        return fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ad_group = self.context.get("ad_group")
        if ad_group and ad_group.bidding_type == constants.BiddingType.CPM:
            ret["cpc"] = None
        elif "cpm" in ret:
            ret["cpm"] = None
        return ret

    source = restapi.serializers.fields.SourceIdSlugField(source="ad_group_source.source")
    cpc = serializers.DecimalField(
        max_digits=10, decimal_places=4, source="local_cpc_cc_proxy", required=False, rounding=decimal.ROUND_HALF_DOWN
    )
    cpm = serializers.DecimalField(
        max_digits=10, decimal_places=4, source="local_cpm_proxy", required=False, rounding=decimal.ROUND_HALF_DOWN
    )
    daily_budget = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        source="local_daily_budget_cc",
        required=False,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    state = restapi.serializers.fields.DashConstantField(constants.AdGroupSourceSettingsState, required=False)
