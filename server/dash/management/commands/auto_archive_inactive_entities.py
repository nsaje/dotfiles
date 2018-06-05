import logging
import datetime

from utils.command_helpers import ExceptionCommand
from utils import dates_helper

from dash import models
from dash import constants

import automation.campaignstop
import redshiftapi.api_breakdowns

logger = logging.getLogger(__name__)

DAYS_INACTIVE = 90


class Command(ExceptionCommand):
    help = "Auto-archive ad groups and campaigns that weren't active in the last 3 months."

    def handle(self, *args, **options):
        adgroups, campaigns = _auto_archive_inactive_entities(
            inactive_since=dates_helper.local_today() - datetime.timedelta(days=DAYS_INACTIVE)
        )
        logger.info('Archived {} ad groups and {} campaigns.'.format(adgroups, campaigns))


def _auto_archive_inactive_entities(inactive_since):
    '''
    Archive groups that:
        - have no spend for the last 90 days AND
        - were last updated more than 90 days ago AND
        - are inactive OR have end date in the past OR campaignstop not allowed to run
    '''

    ad_groups = models.AdGroup.objects.filter(
        settings__created_dt__lte=inactive_since,
        settings__archived=False,
        campaign__account__auto_archiving_enabled=True)\
        .select_related('settings', 'campaign')

    data = redshiftapi.api_breakdowns.query(
        ['ad_group_id'],
        {
            'ad_group_id': [ag.id for ag in ad_groups],
            'date__gte': inactive_since,
        },
        parents=None,
        goals=None,
        use_publishers_view=False,
    )
    grouped_data = {item['ad_group_id']: item for item in data}
    campaigns = set(ag.campaign for ag in ad_groups)
    campaignstop_map = automation.campaignstop.get_campaignstop_states(campaigns)

    for ag in ad_groups:
        campaignstop_allowed_to_run = campaignstop_map[ag.campaign.id]['allowed_to_run']
        spend = grouped_data.get(ag.id, {}).get('etfm_cost', 0)

        if spend == 0 and (
           ag.settings.state == constants.AdGroupSettingsState.INACTIVE or
           not campaignstop_allowed_to_run or
           ag.settings.end_date and ag.settings.end_date < dates_helper.local_today()):

            logger.info('Auto-archived ad group with id {}.'.format(ag.id))
            ag.settings.update_unsafe(
                None,
                archived=True,
                state=constants.AdGroupSettingsState.INACTIVE,
                history_changes_text='Automated archiving.',
            )

    campaigns = models.Campaign.objects.filter(
        settings__created_dt__lte=inactive_since,
        settings__archived=False,
        account__auto_archiving_enabled=True)\
        .exclude(adgroup__settings__archived=False)\
        .select_related('settings')

    campaign_count = 0
    for c in campaigns:
        for budget in c.budgets.all().annotate_spend_data():
            if budget.state() in (constants.BudgetLineItemState.ACTIVE,
                                  constants.BudgetLineItemState.PENDING):
                continue

        logger.info('Auto-archived campaign with id {}.'.format(c.id))
        c.settings.update_unsafe(
            None,
            archived=True,
            history_changes_text='Automated archiving.',
        )
        campaign_count += 1

    return len(ad_groups), campaign_count
