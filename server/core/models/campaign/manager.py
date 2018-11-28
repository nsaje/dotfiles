from django.db import transaction

import core.common
import utils.exc
from dash import constants
from utils import email_helper

from . import model

# These agencies should have campaign stop turned off
# (for example Outbrain)
AGENCIES_WITHOUT_CAMPAIGN_STOP = {55}
ACCOUNTS_WITHOUT_CAMPAIGN_STOP = {490, 512, 513}  # inPowered

ACCOUNTS_WITH_AUTOPILOT_DISABLED = {305}
CAMPAIGN_AUTOPILOT_ENABLED_VALUE = True


class CampaignManager(core.common.BaseManager):
    @transaction.atomic
    def create(
        self,
        request,
        account,
        name,
        iab_category=constants.IABCategory.IAB24,
        language=constants.Language.ENGLISH,
        type=constants.CampaignType.CONTENT,
        send_mail=False,
    ):
        core.common.entity_limits.enforce(model.Campaign.objects.filter(account=account).exclude_archived(), account.id)
        if not account.currency:
            url = request.build_absolute_uri("/v2/analytics/account/{}?settings".format(account.id))
            raise utils.exc.ValidationError(
                data={
                    "message": "You are not able to add a campaign because currency is not defined.",
                    "action": {"text": "Configure the currency", "url": url},
                }
            )
        campaign = model.Campaign(name=name, account=account, type=type)

        campaign.real_time_campaign_stop = True
        if account.id in ACCOUNTS_WITHOUT_CAMPAIGN_STOP or account.agency_id in AGENCIES_WITHOUT_CAMPAIGN_STOP:
            campaign.real_time_campaign_stop = False

        campaign.save(request=request)

        settings_updates = core.models.settings.CampaignSettings.get_defaults_dict()
        settings_updates["name"] = name
        settings_updates["iab_category"] = iab_category
        settings_updates["language"] = language

        if account.id not in ACCOUNTS_WITH_AUTOPILOT_DISABLED:
            settings_updates["autopilot"] = CAMPAIGN_AUTOPILOT_ENABLED_VALUE

        if request:
            settings_updates["campaign_manager"] = request.user

        campaign.settings = core.models.settings.CampaignSettings(campaign=campaign)
        campaign.settings.update(request, **settings_updates)
        campaign.save(request)

        if send_mail:
            email_helper.send_campaign_created_email(request, campaign)

        return campaign
