from rest_framework import serializers

import restapi.fields
import dash.constants
import dash.views.publishers


class PublisherListSerializer(serializers.ListSerializer):

    def to_internal_value(self, data):
        source_slugs = []
        for item in data:
            source_slugs.append(item.get('source'))
        sources = dash.models.Source.objects.filter(bidder_slug__in=source_slugs)
        sources_by_slug = {s.bidder_slug: s for s in sources}
        for item in data:
            source = sources_by_slug.get(item.get('source'))
            if not source:
                raise serializers.ValidationError("Invalid source in object '%s'!" % item)
            item['source'] = source
        ret = super().to_internal_value(data)
        return ret


class PublisherSerializer(serializers.Serializer):
    class Meta:
        list_serializer_class = PublisherListSerializer

    name = restapi.fields.PlainCharField(max_length=127)
    source = restapi.fields.SourceIdSlugField(required=False, allow_null=True)
    status = restapi.fields.DashConstantField(dash.constants.PublisherStatus)
    level = restapi.fields.DashConstantField(dash.constants.PublisherBlacklistLevel, label='level')
    modifier = serializers.FloatField(min_value=0.01, max_value=11.0, required=False, allow_null=True)
