import rest_framework.serializers

import restapi.adgroup.v1.serializers
import restapi.contentad.v1.serializers
import restapi.serializers.base
import restapi.serializers.fields


class AdGroupCustomTargetingSerializer(restapi.adgroup.v1.serializers.AdGroupTargetingSerializer):
    sources = rest_framework.serializers.ListSerializer(child=restapi.serializers.fields.SourceIdSlugField())


class AdGroupCustomSerializer(restapi.adgroup.v1.serializers.AdGroupSerializer):
    class Meta(restapi.adgroup.v1.serializers.AdGroupSerializer.Meta):
        fields = restapi.adgroup.v1.serializers.AdGroupSerializer.Meta.fields + ("ads",)

    ads = restapi.contentad.v1.serializers.ContentAdCandidateSerializer(many=True, required=False)
    targeting = AdGroupCustomTargetingSerializer(source="*", required=False)


class AdGroupCustomResponseSerializer(restapi.adgroup.v1.serializers.AdGroupSerializer):
    class Meta(restapi.adgroup.v1.serializers.AdGroupSerializer.Meta):
        fields = restapi.adgroup.v1.serializers.AdGroupSerializer.Meta.fields + ("ads",)

    ads = restapi.contentad.v1.serializers.ContentAdSerializer(many=True, required=False)
    targeting = AdGroupCustomTargetingSerializer(source="*", required=False)


class TaskStatus(rest_framework.serializers.Serializer):
    task_id = rest_framework.serializers.CharField(max_length=100)
    status = rest_framework.serializers.CharField(max_length=100)
    ad_groups = AdGroupCustomResponseSerializer(many=True)
