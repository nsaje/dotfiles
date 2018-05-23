from restapi.common.views_base import RESTAPIBaseViewSet
from django.db import transaction

import core
import restapi.access
import utils.exc

from . import serializers


class AdGroupSourceViewSet(RESTAPIBaseViewSet):

    def list(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        settings = core.entity.settings.ad_group_source_settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).group_current_settings().select_related('ad_group_source__source')
        serializer = serializers.AdGroupSourceSerializer(settings, many=True)
        return self.response_ok(serializer.data)

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        serializer = serializers.AdGroupSourceSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            ad_group_sources = {}
            sources = []

            for item in serializer.validated_data:
                sources.append(item['ad_group_source']['source'])

            ad_group_sources = core.entity.adgroup.ad_group_source.AdGroupSource.objects.filter(
                ad_group=ad_group,
                source__in=sources,
            ).select_related('settings', 'source')

            ags_by_source = {ags.source: ags for ags in ad_group_sources}

            for item in serializer.validated_data:
                source = item['ad_group_source']['source']
                ad_group_source = ags_by_source.get(source)
                if not ad_group_source:
                    raise utils.exc.ValidationError("Source %s not present on ad group!" % source.name)
                item.pop('ad_group_source')
                ad_group_source.settings.update(request, k1_sync=True, **item)

        return self.list(request, ad_group.id)

    def create(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        serializer = serializers.AdGroupSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            data = serializer.validated_data
            source = data['ad_group_source']['source']
            data.pop('ad_group_source')
            ad_group_source = core.entity.adgroup.ad_group_source.AdGroupSource.objects.create(
                request, ad_group, source,
                write_history=True, k1_sync=False,
                **data
            )

        serializer = serializers.AdGroupSourceSerializer(ad_group_source.get_current_settings())
        return self.response_ok(serializer.data)
