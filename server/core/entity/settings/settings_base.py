# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.db import models
from django.db import transaction

import core.history
from dash import constants

from update_object import UpdateObject


class SettingsBase(models.Model, core.history.HistoryMixin):
    class Meta:
        abstract = True

    created_dt = models.DateTimeField(verbose_name='Created at')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+',
                                   on_delete=models.PROTECT, null=True, blank=True)

    def save(self, *args, **kwargs):
        raise AssertionError('Direct update of settings object not allowed. Use .update()')

    def delete(self, *args, **kwargs):
        raise AssertionError('Deleting settings object not allowed.')

    def _create_copy(self):
        pk = self.pk
        self.pk = None
        super(SettingsBase, self).save()
        self.pk = pk

    def get_changes(self, kwargs):
        changes = {}
        for key, value in kwargs.iteritems():
            if getattr(self, key) != value:
                changes[key] = value
        return changes

    # Real settings model should override this
    # and implement validation and notification of other systems
    def update(self, request, **kwargs):
        self.update_unsafe(request, **kwargs)

    # Unsafe update without validation and notification of other systems
    @transaction.atomic()
    def update_unsafe(self, request, update_fields=None, **kwargs):
        user = request.user if request else None
        changes = self.get_changes(kwargs)

        if self.pk is not None:
            if not changes:
                return
            self._create_copy()

        history_changes = self.get_model_state_changes(kwargs)
        self.add_to_history(user, constants.HistoryActionType.SETTINGS_CHANGE, history_changes)

        self.created_by = user
        self.created_dt = datetime.datetime.utcnow()
        for k, v in changes.iteritems():
            setattr(self, k, v)
        if update_fields is not None:
            update_fields.extend(['created_by', 'created_dt'])
        super(SettingsBase, self).save(update_fields=update_fields)

    def copy_settings(self):
        return UpdateObject(self)

    @classmethod
    def get_settings_fields(cls):
        return cls._settings_fields

    def get_settings_dict(self):
        return {settings_key: getattr(self, settings_key) for settings_key in self._settings_fields}

    def get_setting_changes(self, new_settings):
        if type(new_settings) == UpdateObject:
            return new_settings.get_updates()
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
