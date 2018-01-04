# -*- coding: utf-8 -*-

from django.db import models


class SettingsQuerySet(models.QuerySet):

    def update(self, *args, **kwargs):
        raise AssertionError('Using update not allowed.')

    def delete(self, *args, **kwargs):
        raise AssertionError('Using delete not allowed.')

    def group_current_settings(self):
        return self.filter(latest_for_entity__isnull=False)
