# this is used in copy_settings() to ensure backwards compatibility
class UpdateObject(object):
    def __init__(self, settings):
        self.__dict__['settings'] = settings

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        return getattr(self.settings, key)

    def __setattr__(self, key, value):
        old_value = key in self.__dict__ and self.__dict__[key] or getattr(self.settings, key)

        if value != old_value:
            self.__dict__[key] = value

    def get_updates(self):
        fields = (field.name for field in self.settings._meta.get_fields())
        updates = {key: self.__dict__[key] for key in fields if key in self.__dict__}
        return updates

    def save(self, request=None, action_type=None, changes_text=None, update_fields=None):
        updates = self.get_updates()
        self.settings.update_unsafe(request, update_fields=update_fields, **updates)

    def get_settings_dict(self):
        settings_dict = self.settings.get_settings_dict()
        settings_dict.update(self.get_updates())
        return settings_dict

    def get_setting_changes(self, new_settings):
        if new_settings == self.settings:
            return self.settings.get_dict_changes(
                self.get_settings_dict(),
                self.settings.get_settings_dict(),
                self.settings._settings_fields,
            )
        return self.settings.get_setting_changes(new_settings)
