from restapi.common.views_base import RESTAPIBaseViewSet
import restapi.access

import core.entity.settings.ad_group_settings.exceptions
import core.entity.settings.ad_group_source_settings.exceptions

import utils.exc
import decimal

from . import serializers


class AdGroupSourcesRTBViewSet(RESTAPIBaseViewSet):
    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        return self.response_ok(serializers.AdGroupSourcesRTBSerializer(ad_group.settings).data)

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        serializer = serializers.AdGroupSourcesRTBSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.update_settings(request, ad_group, serializer.validated_data)
        return self.response_ok(serializers.AdGroupSourcesRTBSerializer(ad_group.settings).data)

    def update_settings(self, request, ad_group, settings):
        try:
            ad_group.settings.update(request, **settings)

        except core.entity.settings.ad_group_settings.exceptions.AdGroupNotPaused as err:
            raise utils.exc.ValidationError(errors={"group_enabled": [str(err)]})

        except core.entity.settings.ad_group_settings.exceptions.DailyBudgetAutopilotNotDisabled as err:
            raise utils.exc.ValidationError(errors={"daily_budget": [str(err)]})

        except core.entity.settings.ad_group_settings.exceptions.CPCAutopilotNotDisabled as err:
            raise utils.exc.ValidationError(errors={"daily_budget": [str(err)]})

        except core.entity.settings.ad_group_source_settings.exceptions.RTBSourcesCPCNegative as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except core.entity.settings.ad_group_source_settings.exceptions.RTBSourcesCPMNegative as err:
            raise utils.exc.ValidationError(errors={"cpm": [str(err)]})

        except core.entity.settings.ad_group_source_settings.exceptions.CPCPrecisionExceeded as err:
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

        except core.entity.settings.ad_group_source_settings.exceptions.CPMPrecisionExceeded as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpm": [
                        "CPM on {} cannot exceed {} decimal place{}.".format(
                            err.data.get("source_name"),
                            err.data.get("value"),
                            "s" if err.data.get("value") != 1 else "",
                        )
                    ]
                }
            )

        except core.entity.settings.ad_group_source_settings.exceptions.MinimalCPCTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpc": [
                        "Minimum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.entity.settings.ad_group_source_settings.exceptions.MaximalCPCTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpc": [
                        "Maximum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.entity.settings.ad_group_source_settings.exceptions.MinimalCPMTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpm": [
                        "Minimum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.entity.settings.ad_group_source_settings.exceptions.MaximalCPMTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpm": [
                        "Maximum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except core.entity.settings.ad_group_source_settings.exceptions.DailyBudgetNegative as err:
            raise utils.exc.ValidationError(errors={"daily_budget": [str(err)]})

        except core.entity.settings.ad_group_source_settings.exceptions.MinimalDailyBudgetTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "daily_budget": [
                        "Please provide daily spend cap of at least {}.".format(
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_CEILING, ad_group.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except core.entity.settings.ad_group_source_settings.exceptions.MaximalDailyBudgetTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "daily_budget": [
                        "Maximum allowed daily spend cap is {}. "
                        "If you want use a higher daily spend cap, please contact support.".format(
                            core.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_FLOOR, ad_group.settings.get_currency()
                            )
                        )
                    ]
                }
            )
