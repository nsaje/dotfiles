# -*- coding: utf-8 -*-

from decimal import Decimal

from django.conf import settings
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

from settings_base import SettingsBase
from settings_query_set import SettingsQuerySet


class AdGroupSourceSettings(SettingsBase):

    class Meta:
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)
        app_label = 'dash'

    _settings_fields = [
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'landing_mode'
    ]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)

    ad_group_source = models.ForeignKey(
        'AdGroupSource',
        null=True,
        related_name='settings',
        on_delete=models.PROTECT
    )

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        null=True,
        blank=True,
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
    daily_budget_cc = models.DecimalField(
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
            'daily_budget_cc': 'Daily Spend Cap',
            'landing_mode': 'Landing Mode',
        }
        return NAMES.get(prop_name)

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name == 'state':
            value = constants.AdGroupSourceSettingsState.get_text(value)
        elif prop_name == 'cpc_cc' and value is not None:
            value = lc_helper.default_currency(Decimal(value), places=3)
        elif prop_name == 'daily_budget_cc' and value is not None:
            value = lc_helper.default_currency(Decimal(value))
        elif prop_name == 'landing_mode':
            value = str(value)
        return value

    def save(self, request, action_type=None, *args, **kwargs):
        if self.pk is None and request is not None:
            self.created_by = request.user

        super(AdGroupSourceSettings, self).save(*args, **kwargs)
        self.add_to_history(request and request.user, action_type)

    def add_to_history(self, user, action_type):
        current_settings = self.ad_group_source.ad_group.get_current_settings()

        changes = self.get_model_state_changes(
            self.get_settings_dict()
        )
        _, changes_text = self.construct_changes(
            'Created settings.',
            'Source: {}.'.format(self.ad_group_source.source.name),
            changes
        )
        current_settings.ad_group.write_history(
            changes_text,
            changes=changes,
            user=user,
            action_type=action_type,
            system_user=self.system_user,
        )

    @classmethod
    def get_current_settings(cls, ad_group, sources):
        source_ids = [x.pk for x in sources]

        source_settings = cls.objects.filter(
            ad_group_source__ad_group=ad_group,
        ).order_by('-created_dt')

        result = {}
        for s in source_settings:
            source = s.ad_group_source.source

            if source.id in result:
                continue

            result[source.id] = s

            if len(result) == len(source_ids):
                break

        for sid in source_ids:
            if sid in result:
                continue

            result[sid] = cls(
                state=None,
                ad_group_source=core.entity.AdGroupSource(
                    ad_group=ad_group,
                    source=core.source.Source.objects.get(pk=sid)
                )
            )

        return result

    def get_external_daily_budget_cc(self, account, license_fee, margin):
        daily_budget_cc = self.daily_budget_cc
        if account.uses_bcm_v2:
            daily_budget_cc = core.bcm.calculations.subtract_fee_and_margin(
                daily_budget_cc,
                license_fee,
                margin,
            )
        return daily_budget_cc

    def get_external_cpc_cc(self, account, license_fee, margin):
        cpc_cc = self.cpc_cc
        if account.uses_bcm_v2:
            cpc_cc = core.bcm.calculations.subtract_fee_and_margin(
                cpc_cc,
                license_fee,
                margin,
            )
        return cpc_cc

    class QuerySet(SettingsQuerySet):

        def group_current_settings(self):
            return self.order_by('ad_group_source_id', '-created_dt').distinct('ad_group_source')

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(ad_group_source__source__in=sources)
