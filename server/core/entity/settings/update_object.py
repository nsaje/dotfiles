class UpdateObject(object):
    """ An object returned by `SettingsBase.copy_settings()` that keeps track of proposed
        changes to the settings. Ensures backward compatibility with old settings style.
    """
    def __init__(self, settings):
        self.__dict__['settings'] = settings
        self.__dict__['_supports_multicurrency'] = hasattr(settings, 'get_multicurrency_counterpart')

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        return getattr(self.settings, key)

    def __setattr__(self, key, value):
        old_value = key in self.__dict__ and self.__dict__[key] or getattr(self.settings, key)

        if value != old_value:
            self.__dict__[key] = value
            if self._supports_multicurrency:
                counterpart_key, counterpart_value = self.settings.get_multicurrency_counterpart(key, value)
                if counterpart_key and counterpart_value:
                    self.__dict__[counterpart_key] = counterpart_value

    def get_updates(self):
        fields = (field.name for field in self.settings._meta.get_fields())
        updates = {key: self.__dict__[key] for key in fields if key in self.__dict__}
        return updates

    def save(self, request=None, action_type=None, changes_text=None, update_fields=None, system_user=None):
        updates = self.get_updates()
        self.settings.update_unsafe(request, update_fields=update_fields, system_user=system_user, **updates)

    def get_settings_dict(self):
        settings_dict = self.settings.get_settings_dict()
        settings_dict.update({k: v for k, v in self.get_updates().items() if k in self._settings_fields})
        return settings_dict

    def get_setting_changes(self, new_settings):
        if new_settings == self.settings:
            return self.settings.get_dict_changes(
                self.get_settings_dict(),
                self.settings.get_settings_dict(),
                self.settings._settings_fields,
            )
        return self.settings.get_setting_changes(new_settings)
