
import core.common
from dash import constants
from utils import dates_helper

LEGACY_AGENCY_IDS = [705, 635, 779, 208, 490, 448, 670]


class AdGroupSettingsManager(core.common.QuerySetManager):
    def create_default(self, ad_group, name):
        new_settings = self._create_default_obj(ad_group)
        new_settings.ad_group_name = name
        new_settings.update_unsafe(None)
        return new_settings

    def get_default(self, ad_group, name):
        new_settings = self._create_default_obj(ad_group)
        new_settings.ad_group_name = name
        self._override_settings_with_campaign_goal_value(new_settings, ad_group.campaign)
        return new_settings

    def create_restapi_default(self, ad_group, name):
        new_settings = self._create_default_obj(ad_group)
        new_settings.ad_group_name = name
        new_settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        new_settings.autopilot_daily_budget = 0

        # TODO: RTAP: Remove after defaults updated for everyone
        if ad_group.campaign.account.agency_id in LEGACY_AGENCY_IDS:
            new_settings.b1_sources_group_enabled = False
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.INACTIVE
        else:
            new_settings.b1_sources_group_enabled = True
            new_settings.b1_sources_group_state = constants.AdGroupSourceSettingsState.ACTIVE

        new_settings.update_unsafe(None)
        return new_settings

    def clone(self, request, ad_group, source_ad_group_settings, state_override=None):
        new_settings = self._create_default_obj(ad_group)
        for field in set(self.model._settings_fields) - {"ad_group_name"}:
            setattr(new_settings, field, getattr(source_ad_group_settings, field))

        new_settings.state = source_ad_group_settings.state
        if state_override:
            new_settings.state = state_override

        new_settings.archived = False

        today = dates_helper.local_today()
        if source_ad_group_settings.start_date is not None and source_ad_group_settings.start_date < today:
            new_settings.start_date = today

        if source_ad_group_settings.end_date is not None and source_ad_group_settings.end_date <= today:
            new_settings.end_date = None

        new_settings.update_unsafe(request)
        return new_settings

    def _create_default_obj(self, ad_group):
        from .model import AdGroupSettings

        currency = ad_group.campaign.account.currency
        new_settings = AdGroupSettings(ad_group=ad_group, **AdGroupSettings.get_defaults_dict(currency=currency))
        campaign_settings = ad_group.campaign.get_current_settings()

        new_settings.target_devices = campaign_settings.target_devices
        new_settings.target_os = campaign_settings.target_os
        new_settings.target_environments = campaign_settings.target_environments
        new_settings.target_connection_types = [constants.ConnectionType.WIFI, constants.ConnectionType.CELLULAR]
        new_settings.ad_group_name = ad_group.name
        return new_settings

    def _override_settings_with_campaign_goal_value(self, new_settings, campaign):
        from dash import campaign_goals

        cpc_campaign_goal_value = (
            campaign_goals.get_campaign_goal_values(campaign)
            .filter(campaign_goal__type=constants.CampaignGoalKPI.CPC)
            .first()
        )
        if cpc_campaign_goal_value:
            new_settings.cpc = cpc_campaign_goal_value.value
            new_settings.local_cpc = cpc_campaign_goal_value.local_value
