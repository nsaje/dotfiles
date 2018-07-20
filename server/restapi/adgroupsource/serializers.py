from rest_framework import serializers

from restapi.serializers import fields

from dash import constants
import dash.models


class AdGroupSourceListSerializer(serializers.ListSerializer):
    def to_internal_value(self, data):
        source_slugs = []
        for item in data:
            source_slugs.append(item.get("source"))
        sources = dash.models.Source.objects.filter(bidder_slug__in=source_slugs)
        sources_by_slug = {s.bidder_slug: s for s in sources}
        for item in data:
            source = sources_by_slug.get(item.get("source"))
            if not source:
                raise serializers.ValidationError("Invalid source in object '%s'!" % item)
            item["source"] = source
        ret = super().to_internal_value(data)
        return ret


class AdGroupSourceSerializer(serializers.Serializer):
    class Meta:
        list_serializer_class = AdGroupSourceListSerializer

    source = fields.SourceIdSlugField(source="ad_group_source.source")
    cpc = serializers.DecimalField(max_digits=10, decimal_places=4, source="local_cpc_cc", required=False)
    daily_budget = serializers.DecimalField(
        max_digits=10, decimal_places=4, source="local_daily_budget_cc", required=False
    )
    state = fields.DashConstantField(constants.AdGroupSourceSettingsState, required=False)
