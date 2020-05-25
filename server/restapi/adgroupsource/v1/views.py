import decimal

from django.db import transaction

import core.features.multicurrency
import core.models.ad_group_source
import utils.exc
import utils.lc_helper
import utils.string_helper
import zemauth.access
import zemauth.features.entity_permission.helpers
from core.models.settings.ad_group_source_settings import exceptions
from restapi.adgroupsource.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission


class AdGroupSourceViewSet(RESTAPIBaseViewSet):
    def list(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)
        settings = (
            core.models.settings.ad_group_source_settings.AdGroupSourceSettings.objects.filter(
                ad_group_source__ad_group=ad_group
            )
            .group_current_settings()
            .select_related("ad_group_source__source")
        )
        serializer = serializers.AdGroupSourceSerializer(
            settings, many=True, context={"request": request, "ad_group": ad_group}
        )
        return self.response_ok(serializer.data)

    def put(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)

        serializer = serializers.AdGroupSourceSerializer(
            data=request.data, many=True, context={"request": request, "ad_group": ad_group}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            ad_group_sources = {}
            sources = []

            for item in serializer.validated_data:
                sources.append(item["ad_group_source"]["source"])

            ad_group_sources = core.models.ad_group_source.AdGroupSource.objects.filter(
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
        ad_group = zemauth.access.get_ad_group(request.user, Permission.WRITE, ad_group_id)
        is_many = isinstance(request.data, list)
        serializer = serializers.AdGroupSourceSerializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)

        if is_many:
            new_settings = self._create_bulk(request, ad_group, serializer.validated_data)
        else:
            new_settings = self._create_ad_group_source(request, ad_group, serializer.validated_data)

        return self.response_ok(serializers.AdGroupSourceSerializer(new_settings, many=is_many).data)

    def _create_bulk(self, request, ad_group, data):
        ad_group_sources_settings = []

        with transaction.atomic():
            errors = []
            for entry in data:
                try:
                    ad_group_source = self._create_ad_group_source(request, ad_group, entry)
                    ad_group_sources_settings.append(ad_group_source)

                except utils.exc.ValidationError as e:
                    errors.append(str(e))

            if errors:
                raise utils.exc.ValidationError(errors=errors)

        return ad_group_sources_settings

    def _create_ad_group_source(self, request, ad_group, updates):
        try:
            source = updates["ad_group_source"]["source"]
            updates.pop("ad_group_source")

            ad_group_source = core.models.ad_group_source.AdGroupSource.objects.create(
                request, ad_group, source, write_history=True, k1_sync=False, **updates
            )

        except (
            core.models.ad_group_source.exceptions.SourceNotAllowed,
            core.models.ad_group_source.exceptions.RetargetingNotSupported,
            core.models.ad_group_source.exceptions.SourceAlreadyExists,
            core.models.ad_group_source.exceptions.VideoNotSupported,
            core.models.ad_group_source.exceptions.DisplayNotSupported,
        ) as err:
            raise utils.exc.ValidationError(str(err))

        return ad_group_source.get_current_settings()

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
                            core.features.multicurrency.format_value_in_currency(
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
                        "If you want to use a higher daily spend cap, please contact support.".format(
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 0, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            )
                        )
                    ]
                }
            )

        except exceptions.CPCNegative as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.CPMNegative as err:
            raise utils.exc.ValidationError(errors={"cpm": [str(err)]})

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

        except exceptions.CPMPrecisionExceeded as err:
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

        except exceptions.MinimalCPCTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpc": [
                        "Minimum CPC on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
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
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except exceptions.MinimalCPMTooLow as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpm": [
                        "Minimum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_CEILING, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except exceptions.MaximalCPMTooHigh as err:
            raise utils.exc.ValidationError(
                errors={
                    "cpm": [
                        "Maximum CPM on {} is {}.".format(
                            err.data.get("source_name"),
                            core.features.multicurrency.format_value_in_currency(
                                err.data.get("value"), 2, decimal.ROUND_FLOOR, ad_group_source.settings.get_currency()
                            ),
                        )
                    ]
                }
            )

        except exceptions.CannotSetCPC as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.CannotSetCPM as err:
            raise utils.exc.ValidationError(errors={"cpm": [str(err)]})

        except exceptions.B1SourcesCPCNegative as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.B1SourcesCPMNegative as err:
            raise utils.exc.ValidationError(errors={"cpm": [str(err)]})

        except exceptions.CPCInvalid as err:
            raise utils.exc.ValidationError(errors={"cpc": [str(err)]})

        except exceptions.MediaSourceNotConnectedToFacebook as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})

        except exceptions.AutopilotDailySpendCapTooLow as err:
            raise utils.exc.ValidationError(errors={"state": [str(err)]})
