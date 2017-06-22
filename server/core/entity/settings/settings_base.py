# -*- coding: utf-8 -*-

from django.db import models

import core.common
import core.history

from copy_settings_mixin import CopySettingsMixin


class SettingsBase(models.Model, CopySettingsMixin, core.history.HistoryMixin):
    class Meta:
        abstract = True

    _settings_fields = None

    objects = core.common.QuerySetManager()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise AssertionError('Updating settings object not alowed.')

        super(SettingsBase, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AssertionError('Deleting settings object not allowed.')

    @classmethod
    def get_settings_fields(cls):
        return cls._settings_fields

    def get_settings_dict(self):
        return {settings_key: getattr(self, settings_key) for settings_key in self._settings_fields}

    def set_settings_dict(self, dict):
        for settings_key in self._settings_fields:
            if settings_key in dict:
                setattr(self, settings_key, dict[settings_key])

    def get_setting_changes(self, new_settings):
        current_settings_dict = self.get_settings_dict()
        new_settings_dict = new_settings.get_settings_dict()
        return SettingsBase.get_dict_changes(
            current_settings_dict,
            new_settings_dict,
            self._settings_fields
        )

    @classmethod
    def get_dict_changes(self, current_settings_dict, new_settings_dict, settings_fields):
        changes = {}
        for field_name in settings_fields:
            if current_settings_dict[field_name] != new_settings_dict[field_name]:
                value = new_settings_dict[field_name]
                changes[field_name] = value
        return changes

    @classmethod
    def get_default_value(cls, prop_name):
        return cls.get_defaults_dict().get(prop_name)

    @classmethod
    def get_defaults_dict(cls):
        return {}
