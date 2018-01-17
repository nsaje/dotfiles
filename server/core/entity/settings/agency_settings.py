# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import ArrayField
from django.db import models

import core.common
import core.history
import core.source

from settings_base import SettingsBase
from settings_query_set import SettingsQuerySet


class AgencySettings(SettingsBase):
    class Meta:
        app_label = 'dash'
        ordering = ('-created_dt',)

    _demo_fields = {}

    _settings_fields = [
        'whitelist_publisher_groups',
        'blacklist_publisher_groups',
    ]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)
    agency = models.ForeignKey('Agency', on_delete=models.PROTECT)

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    objects = core.common.QuerySetManager()

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            'whitelist_publisher_groups': 'Whitelist publisher groups',
            'blacklist_publisher_groups': 'Blacklist publisher groups',
        }
        return NAMES[prop_name]

    @classmethod
    def get_human_value(cls, prop_name, value):
        if prop_name in ('whitelist_publisher_groups', 'blacklist_publisher_groups'):
            if not value:
                value = ''
            else:
                names = core.publisher_groups.PublisherGroup.objects.filter(pk__in=value).values_list('name', flat=True)
                value = ', '.join(names)
        return value

    def add_to_history(self, user, action_type, history_changes_text):
        changes = self.get_model_state_changes(
            self.get_settings_dict()
        )
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return

        changes_text = history_changes_text or self.get_changes_text_from_dict(
            changes)
        self.agency.write_history(
            changes_text,
            changes=changes,
            action_type=action_type,
            user=user,
        )

    class QuerySet(SettingsQuerySet):
        pass
