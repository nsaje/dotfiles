# -*- coding: utf-8 -*-

from django.db import models

from dash import constants
import core.audiences
import core.common
import core.entity
import core.history
import core.source

from settings_query_set import SettingsQuerySet
from copy_settings_mixin import CopySettingsMixin


class AdGroupSourceState(models.Model, CopySettingsMixin):
    class Meta:
        app_label = 'dash'
        get_latest_by = 'created_dt'
        ordering = ('-created_dt',)

    _settings_fields = [
        'state',
        'cpc_cc',
        'daily_budget_cc'
    ]

    id = models.AutoField(primary_key=True)

    ad_group_source = models.ForeignKey(
        core.entity.AdGroupSource,
        null=True,
        related_name='states',
        on_delete=models.PROTECT
    )

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')

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

    objects = core.common.QuerySetManager()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise AssertionError('Updating state object not allowed.')

        super(AdGroupSourceState, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssertionError('Deleting object object not allowed.')

    class QuerySet(SettingsQuerySet):

        def group_current_states(self):
            return self.order_by('ad_group_source_id', '-created_dt').distinct('ad_group_source')
