from restapi.views import RESTAPIBaseViewSet
from restapi.common.pagination import StandardPagination
import restapi.access

import core.entity
from core.entity.settings.ad_group_settings import exceptions
from . import serializers
import utils.exc

from django.db import transaction


class AdGroupViewSet(RESTAPIBaseViewSet):

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        return self.response_ok(
            serializers.AdGroupSerializer(ad_group.settings, context={'request': request}).data
        )

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        serializer = serializers.AdGroupSerializer(
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.update_settings(request, ad_group, serializer.validated_data)
        return self.response_ok(
            serializers.AdGroupSerializer(ad_group.settings, context={'request': request}).data
        )

    def list(self, request):
        campaign_id = request.query_params.get('campaignId', None)
        if campaign_id:
            campaign = restapi.access.get_campaign(request.user, campaign_id)
            ad_groups = core.entity.AdGroup.objects.filter(campaign=campaign)
        else:
            ad_groups = core.entity.AdGroup.objects.all().filter_by_user(request.user)

        ad_groups = ad_groups.select_related('settings').order_by('pk')
        paginator = StandardPagination()
        ad_groups_paginated = paginator.paginate_queryset(ad_groups, request)
        paginated_settings = [ad.settings for ad in ad_groups_paginated]
        return paginator.get_paginated_response(
            serializers.AdGroupSerializer(
                paginated_settings, many=True, context={'request': request},
            ).data
        )

    def create(self, request):
        serializer = serializers.AdGroupSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        campaign = restapi.access.get_campaign(
            request.user,
            settings.get('ad_group', {}).get('campaign', {}).get('id')
        )

        with transaction.atomic():
            new_ad_group = core.entity.AdGroup.objects.create(
                request,
                campaign=campaign,
                name=settings.get('ad_group_name', None),
                is_restapi=True,
            )
            self.update_settings(request, new_ad_group, settings)

        return self.response_ok(
            serializers.AdGroupSerializer(new_ad_group.settings, context={'request': request}).data,
            status=201,
        )

    def update_settings(self, request, ad_group, settings):
        try:
            ad_group.settings.update(request, **settings)

        except utils.exc.MultipleValidationError as err:
            errors = {}
            for e in err.errors:
                if isinstance(e, exceptions.MaxCPCTooLow):
                    errors['max_cpc'] = str(e)

                elif isinstance(e, exceptions.MaxCPCTooHigh):
                    errors['max_cpc'] = str(e)

                elif isinstance(e, exceptions.MaxCPMTooLow):
                    errors['max_cpm'] = str(e)

                elif isinstance(e, exceptions.MaxCPMTooHigh):
                    errors['max_cpm'] = str(e)

                elif isinstance(e, exceptions.EndDateBeforeStartDate):
                    errors['end_date'] = str(e)

                elif isinstance(e, exceptions.EndDateInThePast):
                    errors['end_date'] = str(e)

                elif isinstance(e, exceptions.TrackingCodeInvalid):
                    errors['tracking_code'] = str(e)

            raise utils.exc.ValidationError(errors)

        except exceptions.CannotChangeAdGroupState as err:
            raise utils.exc.ValidationError({'state': str(err)})

        except exceptions.AutopilotB1SourcesNotEnabled as err:
            raise utils.exc.ValidationError({'autopilot': {'state': str(err)}})

        except exceptions.AutopilotDailyBudgetTooLow as err:
            raise utils.exc.ValidationError({'autopilot': {'daily_budget': str(err)}})

        except exceptions.AutopilotDailyBudgetTooHigh as err:
            raise utils.exc.ValidationError({'autopilot': {'daily_budget': str(err)}})

        except exceptions.BluekaiCategoryInvalid as err:
            raise utils.exc.ValidationError({'targeting': {'audience': str(err)}})

        except exceptions.YahooDesktopCPCTooLow as err:
            raise utils.exc.ValidationError({'targeting': {'devices': str(err)}})
