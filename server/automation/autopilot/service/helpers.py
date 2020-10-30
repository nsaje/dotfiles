import datetime
from collections import defaultdict

from django.db.models import Q

import dash
import dash.constants
import dash.models
from automation import campaignstop
from automation import models
from utils import zlogging

from .. import settings

logger = zlogging.getLogger(__name__)


def get_active_ad_groups_on_autopilot():
    return dash.models.AdGroup.objects.filter(campaign__settings__autopilot=True).filter_running()


def get_processed_autopilot_campaign_ids(from_date_time):
    return set(
        models.AutopilotLog.objects.filter(created_dt__gte=from_date_time)
        .filter(is_autopilot_job_run=True)
        .values_list("campaign", flat=True)
        .distinct()
    )


def get_autopilot_entities(campaign=None, excluded_campaign_ids=None):
    ad_groups = (
        dash.models.AdGroup.objects.all()
        .filter(campaign__settings__autopilot=True)
        .filter(Q(campaign__account__agency__isnull=False) & Q(campaign__account__agency__uses_realtime_autopilot=True))
        .exclude_archived()
        .select_related("settings", "campaign__settings")
        .distinct()
    )
    if excluded_campaign_ids:
        ad_groups = ad_groups.exclude(campaign__id__in=excluded_campaign_ids)

    if campaign is not None:
        ad_groups = ad_groups.filter(campaign=campaign)
    else:
        ad_groups = ad_groups.filter_active()

    campaignstop_states = campaignstop.get_campaignstop_states(
        dash.models.Campaign.objects.filter(adgroup__in=ad_groups)
    )

    data = defaultdict(list)
    for ag in ad_groups:
        if _should_exclude_ad_group(ag, campaignstop_states, campaign):
            continue
        data[ag.campaign].append(ag)

    return data


def _should_exclude_ad_group(ag, campaignstop_states, campaign):
    # do not process on setting change and not campaign autopilot
    if campaign is not None and not ag.campaign.settings.autopilot:
        return True

    # do not process when adgroup not running
    if ag.get_running_status(ag.settings) != dash.constants.AdGroupRunningStatus.ACTIVE:
        return True

    # on setting change and campaign autopilot process everything but paused adgroups
    if campaign is not None:
        return False

    # do not process adgroups stopped by campaign stop on daily runs
    if ag.campaign.id not in campaignstop_states or not campaignstop_states[ag.campaign.id]["allowed_to_run"]:
        return True

    return False


def ad_group_source_is_synced(ad_group_source):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(hours=settings.SYNC_IS_RECENT_HOURS)
    last_sync = ad_group_source.last_successful_sync_dt
    if last_sync is None:
        return False
    return last_sync >= min_sync_date


def update_ad_group_daily_budget(ad_group, daily_budget):
    ad_group.settings.update(
        None,
        daily_budget=daily_budget,
        skip_validation=True,
        skip_notification=True,
        skip_field_change_validation_autopilot=True,
        system_user=dash.constants.SystemUserType.AUTOPILOT,
        write_source_history=False,
    )


def get_campaign_goal_column(campaign_goal):
    if campaign_goal:
        column_definition = settings.GOALS_COLUMNS[campaign_goal.type]
        return column_definition["col"]


def get_campaign_goal_column_importance(campaign_goal):
    if campaign_goal:
        return settings.GOALS_COLUMNS[campaign_goal.type]["importance"]
