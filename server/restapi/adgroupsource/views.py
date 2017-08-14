from django.db import transaction
from restapi.views import RESTAPIBaseView

import core

import dash.models
from dash.views import helpers

import serializers


class AdGroupSourcesViewList(RESTAPIBaseView):

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        settings = dash.models.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group
        ).group_current_settings().select_related('ad_group_source__source')
        serializer = serializers.AdGroupSourceSerializer(settings, many=True)
        return self.response_ok(serializer.data)

    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        serializer = serializers.AdGroupSourceSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            for item in serializer.validated_data:
                ad_group_source = dash.models.AdGroupSource.objects.get(
                    ad_group=ad_group,
                    source=item['ad_group_source']['source'],
                )
                ad_group_source.update(request, k1_sync=True, **item)

        return self.get(request, ad_group.id)

    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        serializer = serializers.AdGroupSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            ad_group_source = core.entity.AdGroupSource.objects.create(
                request, ad_group, serializer.validated_data['ad_group_source']['source'],
                write_history=True, k1_sync=False,
                **serializer.validated_data
            )

        serializer = serializers.AdGroupSourceSerializer(ad_group_source.get_current_settings())
        return self.response_ok(serializer.data)
