import datetime
import logging

from django.db import transaction

import automation.campaignstop
import redshiftapi.api_breakdowns
import utils.exc
from dash import constants
from dash import models
from utils import dates_helper
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)

DAYS_INACTIVE = 90

WHITELISTED_ACCOUNTS = [305, 490, 512, 513, 293]  # OEN  # InPowered  # -  # -  # BusinessWire


class Command(ExceptionCommand):
    help = "Auto-archive ad groups and campaigns that weren't active in the last 3 months."

    def handle(self, *args, **options):
        adgroups, campaigns = _auto_archive_inactive_entities(
            inactive_since=dates_helper.local_today() - datetime.timedelta(days=DAYS_INACTIVE)
        )
        logger.info("Archived {} ad groups and {} campaigns.".format(adgroups, campaigns))


def _auto_archive_inactive_entities(inactive_since, whitelist=None):
    """
    Archive groups that:
        - have no spend for the last 90 days AND
        - were last updated more than 90 days ago AND
        - are inactive OR have end date in the past OR campaignstop not allowed to run
    """

    ad_groups = models.AdGroup.objects.filter(
        settings__created_dt__lte=inactive_since,
        settings__archived=False,
        campaign__account__auto_archiving_enabled=True,
    ).select_related("settings", "campaign")

    if whitelist:
        ad_groups = ad_groups.filter(campaign__account__id__in=whitelist)

    data = redshiftapi.api_breakdowns.query(
        ["ad_group_id"],
        {"ad_group_id": [ag.id for ag in ad_groups], "date__gte": inactive_since},
        parents=None,
        goals=None,
        use_publishers_view=False,
    )
    grouped_data = {item["ad_group_id"]: item for item in data}
    campaigns = set(ag.campaign for ag in ad_groups)
    campaignstop_map = automation.campaignstop.get_campaignstop_states(campaigns)

    ad_group_count = 0
    for ag in ad_groups:
        campaignstop_allowed_to_run = campaignstop_map[ag.campaign.id]["allowed_to_run"]
        spend = grouped_data.get(ag.id, {}).get("etfm_cost", 0)

        if spend == 0 and (
            ag.settings.state == constants.AdGroupSettingsState.INACTIVE
            or not campaignstop_allowed_to_run
            or ag.settings.end_date
            and ag.settings.end_date < dates_helper.local_today()
        ):
            with transaction.atomic():
                ag.archive(None)
                ag.write_history(changes_text="Automated archiving.")

            logger.info("Auto-archived ad group with id {}.".format(ag.id))
            ad_group_count += 1

    campaigns = (
        models.Campaign.objects.filter(
            settings__created_dt__lte=inactive_since, settings__archived=False, account__auto_archiving_enabled=True
        )
        .exclude(adgroup__settings__archived=False)
        .select_related("settings")
    )

    if whitelist:
        campaigns = campaigns.filter(account__id__in=whitelist)

    campaign_count = 0
    for c in campaigns:
        with transaction.atomic():
            try:
                c.archive(None)
                c.write_history(changes_text="Automated archiving.")

                logger.info("Auto-archived campaign with id {}.".format(c.id))
                campaign_count += 1

            except utils.exc.ForbiddenError:
                continue

    return ad_group_count, campaign_count
