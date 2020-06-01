import core.common
import dash.constants

from . import model


class CampaignSettingsManager(core.common.QuerySetManager):
    def get_default(self, request, campaign, autopilot=False):
        new_settings = model.CampaignSettings(campaign=campaign)
        new_settings.name = campaign.name
        new_settings.language = dash.constants.Language.ENGLISH
        new_settings.autopilot = autopilot
        new_settings.target_devices = dash.constants.AdTargetDevice.get_all()

        if request:
            new_settings.campaign_manager = request.user

        return new_settings

    def clone(self, request, campaign, source_campaign_settings):
        new_settings = self._create_default_obj(campaign)
        for field in set(self.model._settings_fields) - {"name"}:
            setattr(new_settings, field, getattr(source_campaign_settings, field))

        new_settings.archived = False
        new_settings.update_unsafe(request)
        return new_settings

    def _create_default_obj(self, campaign):
        from .model import CampaignSettings

        new_settings = CampaignSettings(campaign=campaign, **CampaignSettings.get_defaults_dict())
        new_settings.name = campaign.name
        return new_settings
