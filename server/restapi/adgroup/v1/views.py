from django.db import transaction

import core.features.delivery_status
import core.models
import core.models.ad_group.exceptions
import utils.converters
import utils.exc
import zemauth.access
from core.models.settings.ad_group_settings import exceptions
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class AdGroupViewSet(RESTAPIBaseViewSet):
    serializer = serializers.AdGroupSerializer

    def get(self, request, ad_group_id):
        qpe = serializers.AdGroupQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)
        include_delivery_status = qpe.validated_data.get("include_delivery_status")
        if include_delivery_status:
            delivery_status = core.features.delivery_status.get_ad_group_delivery_status(ad_group)
            ad_group.settings.delivery_status = delivery_status
        return self.response_ok(self.serializer(ad_group.settings, context={"request": request}).data)

    def put(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data

        with transaction.atomic():
            self._handle_update_create_exceptions(settings, self._update_settings, request, ad_group, settings)

        return self.response_ok(self.serializer(ad_group.settings, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.AdGroupListQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        queryset = core.models.AdGroup.objects.filter_by_entity_permission(request.user, Permission.READ)

        account_id = qpe.validated_data.get("account_id", None)
        if account_id:
            queryset = queryset.filter(campaign__account_id=account_id)

        campaign_id = qpe.validated_data.get("campaign_id", None)
        if campaign_id:
            campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id)
            queryset = queryset.filter(campaign=campaign)

        if not utils.converters.x_to_bool(request.GET.get("includeArchived")):
            queryset = queryset.exclude_archived()

        ad_groups = queryset.select_related("settings").order_by("pk")
        paginator = StandardPagination()
        ad_groups_paginated = paginator.paginate_queryset(ad_groups, request)
        paginated_settings = [ad.settings for ad in ad_groups_paginated]

        include_delivery_status = qpe.validated_data.get("include_delivery_status")
        if include_delivery_status:
            delivery_status_map = core.features.delivery_status.get_ad_group_delivery_status_map(ad_groups_paginated)
            for setting in paginated_settings:
                setting.delivery_status = delivery_status_map.get(setting.ad_group_id)

        return paginator.get_paginated_response(
            self.serializer(paginated_settings, many=True, context={"request": request}).data
        )

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        campaign = zemauth.access.get_campaign(
            request.user, Permission.WRITE, settings.get("ad_group", {}).get("campaign_id")
        )

        with transaction.atomic():
            new_ad_group = self._handle_update_create_exceptions(
                settings,
                core.models.AdGroup.objects.create,
                request,
                campaign=campaign,
                name=settings.get("ad_group_name", None),
                bidding_type=settings.get("ad_group", {}).get("bidding_type"),
                is_restapi=True,
                initial_settings=settings,
            )

        return self.response_ok(self.serializer(new_ad_group.settings, context={"request": request}).data, status=201)

    @staticmethod
    def _update_settings(request, ad_group, settings):
        if settings.get("ad_group", {}).get("bidding_type"):
            ad_group.update(request, bidding_type=settings.get("ad_group", {}).get("bidding_type"))
        ad_group.settings.update(request, **settings)

    @staticmethod
    def _handle_update_create_exceptions(settings, update_function, *args, **kwargs):
        try:
            return AdGroupViewSet._execute_and_handle_exceptions(update_function, *args, **kwargs)
        except utils.exc.ValidationError as e:
            AdGroupViewSet._remap_error_fields_if_needed(settings, e)
            raise

    @staticmethod
    def _remap_error_fields_if_needed(settings, exception):
        if ("bid" in settings or "local_bid" in settings) and getattr(exception, "errors", None):
            max_cpm_error = exception.errors.pop("max_cpm", None)
            if max_cpm_error:
                exception.errors["bid"] = max_cpm_error
            max_cpc_error = exception.errors.pop("max_cpc", None)
            if max_cpc_error:
                exception.errors["bid"] = max_cpc_error

    @staticmethod
    def _execute_and_handle_exceptions(update_function, *args, **kwargs):
        try:
            return update_function(*args, **kwargs)
        except core.models.ad_group.exceptions.CannotChangeBiddingType as err:
            raise utils.exc.ValidationError(errors={"bidding_type": [str(err)]})

        except utils.exc.MultipleValidationError as err:
            errors = {}
            for e in err.errors:
                if isinstance(e, exceptions.CannotSetCPC):
                    errors.setdefault("max_cpc", []).append(str(e))

                elif isinstance(e, exceptions.CannotSetCPM):
                    errors.setdefault("max_cpm", []).append(str(e))

                if isinstance(e, exceptions.CPCTooLow):
                    errors.setdefault("max_cpc", []).append(str(e))

                elif isinstance(e, exceptions.CPCTooHigh):
                    errors.setdefault("max_cpc", []).append(str(e))

                elif isinstance(e, exceptions.CPMTooLow):
                    errors.setdefault("max_cpm", []).append(str(e))

                elif isinstance(e, exceptions.CPMTooHigh):
                    errors.setdefault("max_cpm", []).append(str(e))

                elif isinstance(e, exceptions.EndDateBeforeStartDate):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, exceptions.EndDateInThePast):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, exceptions.TrackingCodeInvalid):
                    errors.setdefault("tracking_code", []).append(str(e))

                elif isinstance(e, exceptions.CannotSetDailyBudgetToUndefined):
                    errors.setdefault("daily_budget", []).append(str(e))

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

        except exceptions.PublisherWhitelistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"included": [str(err)]}}})

        except exceptions.PublisherBlacklistInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"publisherGroups": {"excluded": [str(err)]}}})

        except exceptions.AudienceTargetingInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"customAudiences": {"included": [str(err)]}}})

        except exceptions.ExclusionAudienceTargetingInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"customAudiences": {"excluded": [str(err)]}}})

        except core.models.ad_group.exceptions.CampaignIsArchived as err:
            raise utils.exc.ValidationError(errors={"campaign_id": [str(err)]})

        except exceptions.TargetBrowsersInvalid as err:
            raise utils.exc.ValidationError(errors={"targeting": {"browsers": [str(err)]}})

        except exceptions.CannotSetBidToUndefined as err:
            raise utils.exc.ValidationError(errors={"bid": [str(err)]})

        except exceptions.LegacyFieldsUpdateMismatch as err:
            raise utils.exc.ValidationError(str(err))
