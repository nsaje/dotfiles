from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.common.pagination import StandardPagination
import restapi.access

import core.models
import core.models.ad_group.exceptions
from core.models.settings.ad_group_settings import exceptions
from . import serializers
import utils.exc

from django.db import transaction


class AdGroupViewSet(RESTAPIBaseViewSet):
    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        return self.response_ok(serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data)

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        serializer = serializers.AdGroupSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        self.update_settings(request, ad_group, serializer.validated_data)
        return self.response_ok(serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data)

    def list(self, request):
        campaign_id = request.query_params.get("campaignId", None)
        if campaign_id:
            campaign = restapi.access.get_campaign(request.user, campaign_id)
            ad_groups = core.models.AdGroup.objects.filter(campaign=campaign)
        else:
            ad_groups = core.models.AdGroup.objects.all().filter_by_user(request.user)

        ad_groups = ad_groups.select_related("settings").order_by("pk")
        paginator = StandardPagination()
        ad_groups_paginated = paginator.paginate_queryset(ad_groups, request)
        paginated_settings = [ad.settings for ad in ad_groups_paginated]
        return paginator.get_paginated_response(
            serializers.AdGroupSerializer(paginated_settings, many=True, context={"request": request}).data
        )

    def create(self, request):
        serializer = serializers.AdGroupSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        campaign = restapi.access.get_campaign(request.user, settings.get("ad_group", {}).get("campaign_id"))

        with transaction.atomic():
            new_ad_group = core.models.AdGroup.objects.create(
                request, campaign=campaign, name=settings.get("ad_group_name", None), is_restapi=True
            )
            self.update_settings(request, new_ad_group, settings)

        return self.response_ok(
            serializers.AdGroupSerializer(new_ad_group.settings, context={"request": request}).data, status=201
        )

    def update_settings(self, request, ad_group, settings):
        try:
            ad_group.update_bidding_type(request, settings.get("ad_group", {}).get("bidding_type"))
            ad_group.settings.update(request, **settings)

        except core.models.ad_group.exceptions.CannotChangeBiddingType as err:
            raise utils.exc.ValidationError(errors={"bidding_type": [str(err)]})

        except utils.exc.MultipleValidationError as err:
            errors = {}
            for e in err.errors:
                if isinstance(e, exceptions.CannotSetCPC):
                    errors.setdefault("max_cpc", []).append(str(e))

                elif isinstance(e, exceptions.CannotSetCPM):
                    errors.setdefault("max_cpm", []).append(str(e))

                if isinstance(e, exceptions.MaxCPCTooLow):
                    errors.setdefault("max_cpc", []).append(str(e))

                elif isinstance(e, exceptions.MaxCPCTooHigh):
                    errors.setdefault("max_cpc", []).append(str(e))

                elif isinstance(e, exceptions.MaxCPMTooLow):
                    errors.setdefault("max_cpm", []).append(str(e))

                elif isinstance(e, exceptions.MaxCPMTooHigh):
                    errors.setdefault("max_cpm", []).append(str(e))

                elif isinstance(e, exceptions.EndDateBeforeStartDate):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, exceptions.EndDateInThePast):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, exceptions.TrackingCodeInvalid):
                    errors.setdefault("tracking_code", []).append(str(e))

            raise utils.exc.ValidationError(errors=errors)

        except exceptions.CannotChangeAdGroupState as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})

        except exceptions.AutopilotB1SourcesNotEnabled as err:
            raise utils.exc.ValidationError(errors={"autopilot": {"state": [str(err)]}})

        except exceptions.AutopilotDailyBudgetTooLow as err:
            raise utils.exc.ValidationError(errors={"autopilot": {"daily_budget": [str(err)]}})

        except exceptions.AutopilotDailyBudgetTooHigh as err:
            raise utils.exc.ValidationError(errors={"autopilot": {"daily_budget": [str(err)]}})

        except exceptions.BluekaiCategoryInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"audience": [str(err)]}})

        except exceptions.YahooDesktopCPCTooLow as err:
            raise utils.exc.ValidationError(errors={"targeting": {"devices": [str(err)]}})

        except exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})
