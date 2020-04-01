from rest_framework import serializers

import dash.constants
import dash.views.publishers
import restapi.serializers.fields
from utils import exc


class PublisherListSerializer(serializers.ListSerializer):
    def to_internal_value(self, data):
        source_slugs = []
        for item in data:
            source_slugs.append(item.get("source"))
        sources = dash.models.Source.objects.filter(bidder_slug__in=source_slugs)
        sources_by_slug = {s.bidder_slug: s for s in sources}
        for item in data:
            source_slug = item.get("source")
            source = sources_by_slug.get(source_slug)
            if source_slug and not source:
                raise serializers.ValidationError("Invalid source in object '%s'!" % item)
            item["source"] = source
        ret = super().to_internal_value(data)
        return ret


class PublisherSerializer(serializers.Serializer):
    class Meta:
        list_serializer_class = PublisherListSerializer

    name = restapi.serializers.fields.PlainCharField(max_length=127)
    source = restapi.serializers.fields.SourceIdSlugField(required=False, allow_null=True)
    status = restapi.serializers.fields.DashConstantField(dash.constants.PublisherStatus)
    level = restapi.serializers.fields.DashConstantField(dash.constants.PublisherBlacklistLevel, label="level")
    modifier = serializers.FloatField(min_value=0.01, max_value=11.0, required=False, allow_null=True)

    def validate(self, data):
        if data.get("level") == dash.constants.PublisherBlacklistLevel.ADGROUP:
            if data.get("source") is None and data.get("modifier") is not None:
                raise exc.ValidationError("Modifier can only be set if source is defined")

        return data
