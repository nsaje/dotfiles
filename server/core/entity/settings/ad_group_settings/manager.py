from dash import constants
from utils import dates_helper
import core.common


class AdGroupSettingsManager(core.common.QuerySetManager):

    def _create_default_obj(self, ad_group):
        current_settings = ad_group.get_current_settings()  # get default ad group settings
        new_settings = current_settings.copy_settings()
        campaign_settings = ad_group.campaign.get_current_settings()

        new_settings.target_devices = campaign_settings.target_devices
        new_settings.target_os = campaign_settings.target_os
        new_settings.target_placements = campaign_settings.target_placements
        new_settings.target_regions = campaign_settings.target_regions
        new_settings.ad_group_name = ad_group.name
        return new_settings

    def create_default(self, ad_group, name):
        new_settings = self._create_default_obj(ad_group)
        new_settings.ad_group_name = name
        new_settings.save(None)
        return new_settings

    def create_restapi_default(self, ad_group, name):
        new_settings = self._create_default_obj(ad_group)
        new_settings.ad_group_name = name
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_daily_budget = 0
        new_settings.b1_sources_group_enabled = False
        new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.INACTIVE
        new_settings.save(None)
        return new_settings

    def clone(self, request, ad_group, source_ad_group_settings, state=constants.AdGroupSettingsState.INACTIVE):
        new_settings = self._create_default_obj(ad_group)
        for field in self.model._settings_fields:
            setattr(new_settings, field, getattr(source_ad_group_settings, field))

        new_settings.state = state
        new_settings.archived = False
        if (source_ad_group_settings.end_date is not None and
           source_ad_group_settings.end_date <= dates_helper.local_today()):
            new_settings.start_date = dates_helper.local_today()
            new_settings.end_date = None

        new_settings.save(request)
        return new_settings
