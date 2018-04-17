from django.db import transaction

import core.common

from dash import constants
import utils.exc

from . import model


# These agencies should have campaign stop turned off
# (for example Outbrain)
AGENCIES_WITHOUT_CAMPAIGN_STOP = {55}
ACCOUNTS_WITHOUT_CAMPAIGN_STOP = {490, 512, 513}  # inPowered


class CampaignManager(core.common.BaseManager):

    @transaction.atomic
    def create(self, request, account, name, iab_category=constants.IABCategory.IAB24,
               language=constants.Language.ENGLISH):
        core.common.entity_limits.enforce(
            model.Campaign.objects.filter(account=account).exclude_archived(),
            account.id,
        )
        if not account.currency:
            url = request.build_absolute_uri(
                '/v2/analytics/account/{}?settings'.format(
                    account.id,
                )
            )
            raise utils.exc.ValidationError(
                data={
                    'message': 'You are not able to add a campaign because currency is not defined.',
                    'action': {
                        'text': 'Configure the currency',
                        'url': url,
                    }
                }
            )
        campaign = model.Campaign(
            name=name,
            account=account
        )

        campaign.real_time_campaign_stop = True
        if account.id in ACCOUNTS_WITHOUT_CAMPAIGN_STOP or\
           account.agency_id in AGENCIES_WITHOUT_CAMPAIGN_STOP:
            campaign.real_time_campaign_stop = False

        campaign.save(request=request)

        settings_updates = core.entity.settings.CampaignSettings.get_defaults_dict()
        settings_updates['name'] = name
        settings_updates['iab_category'] = iab_category
        settings_updates['language'] = language
        settings_updates['automatic_campaign_stop'] = False

        if request:
            settings_updates['campaign_manager'] = request.user

        campaign.settings = core.entity.settings.CampaignSettings(campaign=campaign)
        campaign.settings.update(
            request,
            **settings_updates)

        campaign.settings_id = campaign.settings.id
        campaign.save(request)

        return campaign
