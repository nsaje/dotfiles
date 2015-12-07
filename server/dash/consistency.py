
from dash import models


class SettingsStateConsistence(object):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source
        assert type(self.ad_group_source) is models.AdGroupSource

    def is_consistent(self):
        latest_state = self.get_latest_state()
        if latest_state is None:
            return True
        latest_settings = self.ad_group_source.get_current_settings_or_none()
        if latest_settings is None:
            return False
        if latest_settings.created_dt < latest_state.created_dt \
            and any([
                latest_state.state != latest_settings.state,
                latest_state.cpc_cc != latest_settings.cpc_cc,
                latest_state.daily_budget_cc != latest_settings.daily_budget_cc
            ]):
                return False
        return True

    def get_needed_state_updates(self):
        latest_state = self.get_latest_state()
        latest_settings = self.ad_group_source.get_current_settings_or_none()

        changes = {}
        if not latest_settings:
            return changes

        for attr_name in ('state', 'daily_budget_cc', 'cpc_cc'):
            state_val = (getattr(latest_state, attr_name) if latest_state else
                         models.AdGroupSourceSettings._meta.get_field(attr_name).get_default())

            settings_val = getattr(latest_settings, attr_name)
            if state_val != settings_val:
                changes[attr_name] = settings_val

        return changes

    def get_latest_state(self):
        try:
            latest_state = models.AdGroupSourceState.objects \
                .filter(ad_group_source=self.ad_group_source) \
                .latest('created_dt')
            return latest_state
        except models.AdGroupSourceState.DoesNotExist:
            return None
