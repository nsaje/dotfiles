import core.common
import dash.constants

from . import model


class CampaignSettingsManager(core.common.QuerySetManager):
    def get_restapi_default(self, request, campaign, autopilot=False):
        new_settings = model.CampaignSettings(campaign=campaign)
        new_settings.name = campaign.name
        new_settings.iab_category = dash.constants.IABCategory.IAB24
        new_settings.language = dash.constants.Language.ENGLISH
        new_settings.autopilot = autopilot
        new_settings.target_devices = dash.constants.AdTargetDevice.get_all()
        new_settings.target_regions = ["US"]

        if request:
            new_settings.campaign_manager = request.user

        return new_settings
