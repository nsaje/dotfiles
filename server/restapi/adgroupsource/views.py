from restapi.common.views_base import RESTAPIBaseViewSet
import restapi.access

from django.db import transaction

import core.multicurrency
import core.entity.adgroup.ad_group_source
from core.entity.settings.ad_group_source_settings import exceptions

import utils.exc
import utils.lc_helper
import utils.string_helper

import decimal

from . import serializers


class AdGroupSourceViewSet(RESTAPIBaseViewSet):
    def list(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        settings = (
            core.entity.settings.ad_group_source_settings.AdGroupSourceSettings.objects.filter(
                ad_group_source__ad_group=ad_group
            )
            .group_current_settings()
            .select_related("ad_group_source__source")
        )
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
                sources.append(item["ad_group_source"]["source"])

            ad_group_sources = core.entity.adgroup.ad_group_source.AdGroupSource.objects.filter(
                ad_group=ad_group, source__in=sources
            ).select_related("settings", "source")

            ags_by_source = {ags.source: ags for ags in ad_group_sources}

            for item in serializer.validated_data:
                source = item["ad_group_source"]["source"]
                ad_group_source = ags_by_source.get(source)
                if not ad_group_source:
                    raise utils.exc.ValidationError("Source %s not present on ad group!" % source.name)
                item.pop("ad_group_source")
                self._update_ad_group_source(request, ad_group_source, item)

        return self.list(request, ad_group.id)

    def create(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        serializer = serializers.AdGroupSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            data = serializer.validated_data
            source = data["ad_group_source"]["source"]
            data.pop("ad_group_source")
            ad_group_source = core.entity.adgroup.ad_group_source.AdGroupSource.objects.create(
                request, ad_group, source, write_history=True, k1_sync=False, **data
            )

        serializer = serializers.AdGroupSourceSerializer(ad_group_source.get_current_settings())
        return self.response_ok(serializer.data)

    def _update_ad_group_source(self, request, ad_group_source, data):
        try:
            ad_group_source.settings.update(request, k1_sync=True, **data)

        except exceptions.DailyBudgetNegative as err:
            raise utils.exc.ValidationError(errors={"daily_budget": [str(err)]})

        except exceptions.MinimalDailyBudgetTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "daily_budget": [
                        "Please provide daily spend cap of at least {}.".format(
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except exceptions.MaximalDailyBudgetTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "daily_budget": [
                        "Maximum allowed daily spend cap is {}. "
                        "If you want use a higher daily spend cap, please contact support.".format(
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except exceptions.CPCNegative as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.CPCPrecisionExceeded as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpc": [
                        "CPC on {} cannot exceed {} decimal place{}.".format(
                            err.data.get("source_name"),
                            err.data.get("value"),
                            "s" if err.data.get("value") != 1 else "",
                        )
                    ]
                }
            )

        except exceptions.MinimalCPCTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpc": [
                        "Minimum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except exceptions.MaximalCPCTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpc": [
                        "Maximum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except exceptions.RTBSourcesCPCNegative as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.CPCInvalid as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.RetargetingNotSupported as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})

        except exceptions.MediaSourceNotConnectedToFacebook as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})

        except exceptions.YahooCPCTooLow as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})

        except exceptions.AutopilotDailySpendCapTooLow as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})
