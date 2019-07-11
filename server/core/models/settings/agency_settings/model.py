# -*- coding: utf-8 -*-

from django.contrib.postgres.fields import ArrayField
from django.db import models

import core.common
import core.models

from ..settings_base import SettingsBase
from ..settings_query_set import SettingsQuerySet
from . import instance


class AgencySettings(instance.AgencySettingsMixin, SettingsBase):
    class Meta:
        app_label = "dash"
        ordering = ("-created_dt",)

    _demo_fields = {}

    _settings_fields = ["whitelist_publisher_groups", "blacklist_publisher_groups"]
    history_fields = list(_settings_fields)

    id = models.AutoField(primary_key=True)
    agency = models.ForeignKey("Agency", on_delete=models.PROTECT)

    whitelist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)
    blacklist_publisher_groups = ArrayField(models.PositiveIntegerField(), blank=True, default=list)

    objects = core.common.QuerySetManager()

    class QuerySet(SettingsQuerySet):
        pass
