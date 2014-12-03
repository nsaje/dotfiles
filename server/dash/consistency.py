
from dash import models


class SettingsStateConsistence(object):

    def __init__(self, ad_group_source):
        self.ad_group_source = ad_group_source
        assert type(self.ad_group_source) is models.AdGroupSource

    def is_consistent(self):
        latest_state = self.get_latest_state()
        if latest_state is None:
            return True
        latest_settings = self.get_latest_settings()
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

    def get_latest_state(self):
        try:
            latest_state = models.AdGroupSourceState.objects \
                .filter(ad_group_source=self.ad_group_source) \
                .latest('created_dt')
            return latest_state
        except models.AdGroupSourceState.DoesNotExist:
            return None

    def get_latest_settings(self):
        try:
            latest_settings = models.AdGroupSourceSettings.objects \
                .filter(ad_group_source=self.ad_group_source) \
                .latest('created_dt')
            return latest_settings
        except models.AdGroupSourceSettings.DoesNotExist:
            return None