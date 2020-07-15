# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db import transaction

import core.features.history
import core.signals
from dash import constants
from utils import dates_helper
from utils.settings_fields import resolve_related_model_field_name

from .update_object import UpdateObject


class SettingsBase(models.Model, core.features.history.HistoryMixin):
    class Meta:
        abstract = True

    created_dt = models.DateTimeField(verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        raise AssertionError("Direct update of settings object not allowed. Use .update()")

    def delete(self, *args, **kwargs):
        raise AssertionError("Deleting settings object not allowed.")

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
        return self.update_unsafe(request, **kwargs)

    # Unsafe update without validation and notification of other systems
    @transaction.atomic()
    def update_unsafe(self, request, system_user=None, write_history=True, **kwargs):
        user = request.user if request else None
        history_changes_text = kwargs.pop("history_changes_text", None)
        changes = self.get_changes(kwargs)

        update_fields = None
        if self.pk is not None:
            if not changes:
                return
            update_fields = list(changes.keys())
            self._create_copy()

        self.created_by = user
        self.created_dt = dates_helper.utc_now()
        if update_fields is not None:
            update_fields.extend(["created_by", "created_dt"])
        if self.has_field("system_user"):
            self.system_user = system_user
            if update_fields is not None:
                update_fields.append("system_user")

        history_changes = self.get_model_state_changes(kwargs)
        if write_history:
            if history_changes_text:
                self.add_to_history(
                    user, constants.HistoryActionType.SETTINGS_CHANGE, history_changes, history_changes_text
                )
            else:
                self.add_to_history(user, constants.HistoryActionType.SETTINGS_CHANGE, history_changes)

        for k, v in changes.items():
            setattr(self, k, v)
        super(SettingsBase, self).save(update_fields=update_fields)
        self._update_source_settings_reference()
        core.signals.settings_change.send_robust(sender=self.__class__, request=request, instance=self, changes=kwargs)
        return changes

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
        return SettingsBase.get_dict_changes(current_settings_dict, new_settings_dict, self._settings_fields)

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

    @classmethod
    def has_field(cls, name):
        try:
            cls._meta.get_field(name)
            return True
        except FieldDoesNotExist:
            return False

    def _update_source_settings_reference(self):
        """
        When saving a SettingBase instance the source field settings_id reference
        has to be updated in order to avoid deleting settings from field cache.
        """
        field_name = resolve_related_model_field_name(self)
        if field_name:
            source_field = getattr(self, field_name)
            if self.pk is not None and source_field.settings_id is None:
                # SettingsBase has been saved, but settings_id has not been updated yet.
                source_field.settings_id = self.pk
