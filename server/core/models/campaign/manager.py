from django.conf import settings
from django.db import transaction

import core.common
import core.features.bcm
import core.features.goals
import core.models
import core.models.helpers
import utils.exc
from dash import constants
from utils import email_helper

from . import exceptions
from . import model

# These agencies should have campaign stop turned off
# (for example Outbrain)
AGENCIES_WITHOUT_CAMPAIGN_STOP = {55, 663, 635}  # OEN  # FrontStory # PubOcean
ACCOUNTS_WITHOUT_CAMPAIGN_STOP = {
    settings.HARDCODED_ACCOUNT_ID_INPOWERED_1,
    settings.HARDCODED_ACCOUNT_ID_INPOWERED_2,
    settings.HARDCODED_ACCOUNT_ID_INPOWERED_3,
}  # inPowered

ACCOUNTS_WITH_AUTOPILOT_DISABLED = {settings.HARDCODED_ACCOUNT_ID_OEN, settings.HARDCODED_ACCOUNT_ID_INPOWERED_1}
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
        self._validate_archived(account)
        self._validate_entity_limits(account)
        self._validate_currency(request, account)

        campaign = self._prepare(account, name, type)
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

    def clone(self, request, source_campaign, new_name, clone_budget=False):
        core.common.entity_limits.enforce(
            model.Campaign.objects.filter(account=source_campaign.account).exclude_archived(),
            source_campaign.account.id,
        )

        with transaction.atomic():
            campaign = self._prepare(source_campaign.account, new_name, source_campaign.type)
            for field in set(self.model._clone_fields):
                setattr(campaign, field, getattr(source_campaign, field))
            campaign.save(request)

            campaign.settings = core.models.settings.CampaignSettings.objects.clone(
                request, campaign, source_campaign.get_current_settings()
            )
            campaign.save(request)

            if clone_budget:
                for budget in source_campaign.budgets.all().filter_today():
                    core.features.bcm.BudgetLineItem.objects.clone(request, budget, campaign)

            for campaign_goal in source_campaign.campaigngoal_set.all():
                core.features.goals.CampaignGoal.objects.clone(request, campaign_goal, campaign)

            for deal_connection in source_campaign.directdealconnection_set.all():
                core.features.deals.DirectDealConnection.objects.clone(request, deal_connection, campaign=campaign)

        return campaign

    def get_default(self, request, account):
        autopilot = False
        if account.id not in ACCOUNTS_WITH_AUTOPILOT_DISABLED:
            autopilot = CAMPAIGN_AUTOPILOT_ENABLED_VALUE
        campaign = self._prepare(account, "", constants.CampaignType.CONTENT)
        campaign.settings = core.models.settings.CampaignSettings.objects.get_default(request, campaign, autopilot)
        return campaign

    def _create_default_name(self, account):
        return core.models.helpers.create_default_name(model.Campaign.objects.filter(account=account), "New campaign")

    def _prepare(self, account, name, type):
        campaign = model.Campaign(name=name, account=account, type=type)
        campaign.real_time_campaign_stop = True
        if account.id in ACCOUNTS_WITHOUT_CAMPAIGN_STOP or account.agency_id in AGENCIES_WITHOUT_CAMPAIGN_STOP:
            campaign.real_time_campaign_stop = False
        return campaign

    def _validate_archived(self, account):
        if account.is_archived():
            raise exceptions.AccountIsArchived("Can not create a campaign on an archived account.")

    def _validate_entity_limits(self, account):
        core.common.entity_limits.enforce(model.Campaign.objects.filter(account=account).exclude_archived(), account.id)

    def _validate_currency(self, request, account):
        if not account.currency:
            url = request.build_absolute_uri("/v2/analytics/account/{}?settings".format(account.id))
            raise utils.exc.ValidationError(
                data={
                    "message": "You are not able to add a campaign because currency is not defined.",
                    "action": {"text": "Configure the currency", "url": url},
                }
            )
