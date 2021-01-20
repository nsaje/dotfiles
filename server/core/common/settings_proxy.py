import django.utils.functional


class SettingsLazyProxy(django.utils.functional.SimpleLazyObject):
    def update(self, *args, **kwargs):
        if self._wrapped is django.utils.functional.empty:
            self._setup()
        new_settings = self._wrapped.update(*args, **kwargs)
        assert new_settings is not None
        self._wrapped = new_settings


class SettingsProxyMixin(object):
    """ A mixin that enables an entity to access (& update if supported)
        its settings, normally accessable via get_current_settings, via
        .settings property.

        Should become obsolete if/when we introduce FKs to latest settings.
    """

    _current_settings = None

    @property
    def settings(self):
        if self._current_settings:
            return self._current_settings
        self._current_settings = SettingsLazyProxy(self.get_current_settings)
        return self._current_settings
