# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.db import models
from django.db import transaction

import core.history
import core.signals
from dash import constants

from .update_object import UpdateObject


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

    def __getattr__(self, key):
        model_to_field = {
            'adgroupsource': 'ad_group_source',
            'adgroup': 'ad_group',
            'campaign': 'campaign',
            'account': 'account',
            'agency': 'agency',
        }
        model_name = self._meta.get_field('latest_for_entity').related_model._meta.model_name
        field_name = model_to_field[model_name]
        # latest_for_entity is auto populated when entity is loaded with select_related settings
        # this ensures settings.entity can use same optimization
        if key == self._meta.get_field(field_name).get_cache_name():
            v = getattr(self, self._meta.get_field('latest_for_entity').get_cache_name())
            setattr(self, key, v)
            return v
        raise AttributeError("%r object has no attribute %r" % (self.__class__, key))

    def _create_copy(self):
        pk = self.pk
        self.pk = None
        super(SettingsBase, self).save()
        self.pk = pk

    def get_changes(self, kwargs):
        changes = {}
        for key, value in kwargs.items():
            if getattr(self, key) != value:
                changes[key] = value
        return changes

    # Real settings model should override this
    # and implement validation and notification of other systems
    def update(self, request, **kwargs):
        self.update_unsafe(request, **kwargs)

    # Unsafe update without validation and notification of other systems
    @transaction.atomic()
    def update_unsafe(self, request, update_fields=None, system_user=None, **kwargs):
        user = request.user if request else None
        changes = self.get_changes(kwargs)

        if self.pk is not None:
            if not changes:
                return
            self._create_copy()

        self.created_by = user
        self.created_dt = datetime.datetime.utcnow()
        self.system_user = system_user

        history_changes = self.get_model_state_changes(kwargs)
        self.add_to_history(user, constants.HistoryActionType.SETTINGS_CHANGE, history_changes)

        for k, v in changes.items():
            setattr(self, k, v)
        if update_fields is not None:
            update_fields.extend(['created_by', 'created_dt', 'system_user'])
        super(SettingsBase, self).save(update_fields=update_fields)
        core.signals.settings_change.send_robust(
            sender=self.__class__, request=request,
            instance=self, changes=kwargs)

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
