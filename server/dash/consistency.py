
from dash import models
from dash import constants


class SettingsStateConsistence(object):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source
        assert type(self.ad_group_source) is models.AdGroupSource

    def is_consistent(self):
        latest_state = self._get_latest_state()
        latest_settings = self.ad_group_source.get_current_settings_or_none()

        if latest_state is None:
            return True

        if latest_settings is None:
            return False

        if latest_settings.created_dt > latest_state.created_dt:
            return True

        return not self._get_state_changes(latest_state, latest_settings)

    def get_needed_state_updates(self):
        latest_state = self._get_latest_state()
        latest_settings = self.ad_group_source.get_current_settings_or_none()
        return self._get_state_changes(latest_state, latest_settings)

    def _get_state_changes(self, state, settings):
        changes = {}
        if not settings:
            return changes

        for attr_name in ('daily_budget_cc', 'cpc_cc'):
            state_val = self._get_state_value(state, attr_name)
            settings_val = getattr(settings, attr_name)
            if state_val != settings_val:
                changes[attr_name] = settings_val

        actual_settings_state = self._get_actual_source_settings_state(settings)
        latest_state_state = self._get_state_value(state, 'state')
        if actual_settings_state != latest_state_state:
            changes['state'] = actual_settings_state

        return changes

    def _get_state_value(self, state, attr_name):
        return (getattr(state, attr_name) if state else
                models.AdGroupSourceSettings._meta.get_field(attr_name).get_default())

    def _get_actual_source_settings_state(self, settings):
        ad_group = settings.ad_group_source.ad_group
        ad_group_settings = ad_group.get_current_settings()
        if ad_group_settings.state == constants.AdGroupSettingsState.INACTIVE:
            return constants.AdGroupSourceSettingsState.INACTIVE
        else:
            return settings.state

    def _get_latest_state(self):
        try:
            latest_state = models.AdGroupSourceState.objects \
                .filter(ad_group_source=self.ad_group_source) \
                .latest('created_dt')
            return latest_state
        except models.AdGroupSourceState.DoesNotExist:
            return None
