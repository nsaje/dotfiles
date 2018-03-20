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
import core.history
import core.source

from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from .. import multicurrency_mixin

from .instance import AdGroupSourceSettingsMixin
from .validation import AdGroupSourceSettingsValidatorMixin


class AdGroupSourceSettings(AdGroupSourceSettingsMixin,
                            AdGroupSourceSettingsValidatorMixin,
                            multicurrency_mixin.MulticurrencySettingsMixin,
                            SettingsBase):

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)
        app_label = 'dash'

    _settings_fields = [
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'local_cpc_cc',
        'local_daily_budget_cc',
        'landing_mode'
    ]
    multicurrency_fields = [
        'cpc_cc',
        'daily_budget_cc',
    ]
    # TODO(nsaje): switch from excluding local fields to excluding usd fields at multicurrency release
    history_fields = list(set(_settings_fields) - set(['local_%s' % field for field in multicurrency_fields]))

    id = models.AutoField(primary_key=True)

    ad_group_source = models.ForeignKey(
        'AdGroupSource',
        null=True,
        on_delete=models.PROTECT
    )

    system_user = models.PositiveSmallIntegerField(
        choices=constants.SystemUserType.get_choices(),
        null=True,
        blank=True,
    )

    state = models.IntegerField(
        default=constants.AdGroupSourceSettingsState.INACTIVE,
        choices=constants.AdGroupSourceSettingsState.get_choices()
    )
    cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='CPC'
    )
    local_cpc_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='CPC'
    )
    daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Daily spend cap'
    )
    local_daily_budget_cc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Daily spend cap'
    )

    landing_mode = models.BooleanField(default=False)

    objects = core.common.QuerySetManager()

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'state': 'State',
            'cpc_cc': 'CPC',
            'local_cpc_cc': 'CPC',
            'daily_budget_cc': 'Daily Spend Cap',
            'local_daily_budget_cc': 'Daily Spend Cap',
            'landing_mode': 'Landing Mode',
        }
        return NAMES.get(prop_name)

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'state':
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == 'cpc_cc' and value is not None:
            value = lc_helper.default_currency(Decimal(value), places=3)
        elif prop_name == 'local_cpc_cc' and value is not None:
            value = lc_helper.default_currency(Decimal(value), places=3)
        elif prop_name == 'daily_budget_cc' and value is not None:
            value = lc_helper.default_currency(Decimal(value))
        elif prop_name == 'local_daily_budget_cc' and value is not None:
            value = lc_helper.default_currency(Decimal(value))
        elif prop_name == 'landing_mode':
            value = str(value)
        return value

    class QuerySet(SettingsQuerySet):

        def latest_per_entity(self):
            return self.order_by('ad_group_source_id', '-created_dt').distinct('ad_group_source')

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(ad_group_source__source__in=sources)
