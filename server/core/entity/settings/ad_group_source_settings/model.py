# -*- coding: utf-8 -*-

from decimal import Decimal

from django.db import models

from dash import constants
from utils import lc_helper

import core.bcm.calculations
import core.entity
import core.entity.helpers
import core.audiences
import core.common
import core.multicurrency
import core.history
import core.source

from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from .. import multicurrency_mixin

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

    id = models.AutoField(primary_key=True)

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
        currency_symbol = core.multicurrency.get_currency_symbol(self.get_currency())
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
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(ad_group_source__source__in=sources)
