# -*- coding: utf-8 -*-

from decimal import Decimal

from django.db import models
from django.utils.functional import cached_property

import core.common
import core.features.audiences
import core.features.bcm.calculations
import core.features.history
import core.features.multicurrency
import core.models
import core.models.helpers
from core.features import bid_modifiers
from dash import constants
from utils import decimal_helpers
from utils import lc_helper

from .. import multicurrency_mixin
from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from .instance import AdGroupSourceSettingsMixin
from .validation import AdGroupSourceSettingsValidatorMixin


class AdGroupSourceSettings(
    AdGroupSourceSettingsMixin,
    AdGroupSourceSettingsValidatorMixin,
    multicurrency_mixin.MulticurrencySettingsMixin,
    SettingsBase,
):
    class Meta:
        get_latest_by = "created_dt"
        ordering = ("-created_dt",)
        app_label = "dash"

    _settings_fields = [
        "state",
        "cpc_cc",
        "cpm",
        "daily_budget_cc",
        "local_cpc_cc",
        "local_cpm",
        "local_daily_budget_cc",
    ]
    multicurrency_fields = ["cpc_cc", "cpm", "daily_budget_cc"]
    history_fields = list(set(_settings_fields) - set(multicurrency_fields))

    id = models.BigAutoField(primary_key=True)

    ad_group_source = models.ForeignKey("AdGroupSource", null=True, on_delete=models.PROTECT)

    system_user = models.PositiveSmallIntegerField(
        choices=constants.SystemUserType.get_choices(), null=True, blank=True
    )

    state = models.IntegerField(
        default=constants.AdGroupSourceSettingsState.INACTIVE,
        choices=constants.AdGroupSourceSettingsState.get_choices(),
    )
    cpc_cc = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="CPC")
    local_cpc_cc = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="CPC")
    cpm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="CPM")
    local_cpm = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="CPM")
    daily_budget_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Daily spend cap"
    )
    local_daily_budget_cc = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True, verbose_name="Daily spend cap"
    )

    landing_mode = models.NullBooleanField(default=False, blank=True, null=True)

    objects = core.common.QuerySetManager()

    @property
    def local_cpc_cc_proxy(self):
        return self._calculate_bid(self.ad_group_source.ad_group.settings.local_cpc)

    @property
    def local_cpm_proxy(self):
        return self._calculate_bid(self.ad_group_source.ad_group.settings.local_cpm)

    def _calculate_bid(self, bid):
        if bid is None:
            # If ad group bid is undefined (unlimited autopilot), source bids are not defined.
            return None

        return decimal_helpers.multiply_as_decimals(bid, self.bid_modifier)

    @cached_property
    def bid_modifier(self):
        bid_modifier = (
            bid_modifiers.BidModifier.objects.only("modifier")
            .filter(
                type=bid_modifiers.BidModifierType.SOURCE,
                ad_group=self.ad_group_source.ad_group,
                target=str(self.ad_group_source.source.id),
            )
            .first()
        )

        if bid_modifier is None:
            return Decimal("1.0000")

        return Decimal(bid_modifier.modifier)

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            "state": "State",
            "cpc_cc": "CPC",
            "cpm": "CPM",
            "local_cpc_cc": "CPC",
            "local_cpm": "CPM",
            "daily_budget_cc": "Daily Spend Cap",
            "local_daily_budget_cc": "Daily Spend Cap",
        }
        return NAMES.get(prop_name)

    def get_human_value(self, prop_name, value):
        currency_symbol = core.features.multicurrency.get_currency_symbol(self.get_currency())
        if prop_name == "state":
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == "local_cpc_cc" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=3, curr=currency_symbol)
        elif prop_name == "local_cpm" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=3, curr=currency_symbol)
        elif prop_name == "local_daily_budget_cc" and value is not None:
            value = lc_helper.format_currency(Decimal(value), places=2, curr=currency_symbol)
        return value

    class QuerySet(SettingsQuerySet):
        def latest_per_entity(self):
            return self.order_by("ad_group_source_id", "-created_dt").distinct("ad_group_source")

        def filter_by_sources(self, sources):
            if not core.models.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(ad_group_source__source__in=sources)
