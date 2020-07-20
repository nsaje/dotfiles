import itertools
import operator
from collections import defaultdict
from typing import Dict
from typing import List
from typing import Sequence

from django.db.models import Q

import core.models
import dash.constants
import redshiftapi.api_breakdowns
from utils import dates_helper

from .. import constants
from .. import models
from . import exceptions


def ensure_ad_group_valid(rule: models.Rule, ad_group: core.models.AdGroup):
    if rule.action_type in [constants.ActionType.INCREASE_BUDGET, constants.ActionType.DECREASE_BUDGET]:
        if ad_group.campaign.settings.autopilot:
            raise exceptions.CampaignAutopilotActive("Campaign autopilot must not be active")
        if ad_group.settings.autopilot_state != dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET:
            raise exceptions.BudgetAutopilotInactive("Budget autopilot must be active")


def get_rules_by_ad_group_map(
    rules: Sequence[models.Rule], *, filter_active: bool = True, exclude_inactive_yesterday: bool = False
) -> Dict[core.models.AdGroup, List[models.Rule]]:
    rules_map: Dict[core.models.AdGroup, List[models.Rule]] = defaultdict(list)
    for rule in rules:
        ad_groups = core.models.AdGroup.objects.filter(
            Q(campaign__account__in=rule.accounts_included.all())
            | Q(campaign__in=rule.campaigns_included.all())
            | Q(id__in=rule.ad_groups_included.all())
        ).exclude_archived()

        if filter_active:
            ad_groups = ad_groups.filter_active()

        for ad_group in ad_groups:
            rules_map[ad_group].append(rule)

    if exclude_inactive_yesterday:
        _remove_inactive_ad_groups(rules_map)
    return rules_map


def _remove_inactive_ad_groups(rules_map):
    ad_groups = list(rules_map.keys())
    yesterday_spend_by_ad_group_id = _get_yesterday_spend_by_ad_group_id(ad_groups)
    time_active_yesterday_per_ad_group_id = _get_time_active_yesterday_per_ad_group_id(ad_groups)
    for ad_group in ad_groups:
        if (
            yesterday_spend_by_ad_group_id.get(ad_group.id, 0) == 0
            and time_active_yesterday_per_ad_group_id[ad_group.id] < 60 * 60 * 2
        ):
            del rules_map[ad_group]


def _get_yesterday_spend_by_ad_group_id(ad_groups):
    yesterday = dates_helper.local_yesterday()
    rows = redshiftapi.api_breakdowns.query(
        ["ad_group_id"],
        {"date__lte": yesterday, "date__gte": yesterday, "ad_group_id": [ad_group.id for ad_group in ad_groups]},
        parents=None,
        goals=None,
    )
    return {row["ad_group_id"]: row["local_yesterday_etfm_cost"] for row in rows}


def _get_time_active_yesterday_per_ad_group_id(ad_groups):
    """
    The goal is to find exact time the ad group was set to active previous day. This can
    be achieved by looking at every settings entry in order of creation and adding the
    time between previous and current settings if previous state was set to active. Special
    care has to be taken around the start and end of day. If ad group was active at day
    start the interval from midnight to first settings should be added, similar if it
    was active at the end of day. Represented visually:

    -----X----|////////0-----X////0-----------------------X//////////////////|---0--------

    |: midnight
    X: settings set to active
    0: settings set to inactive
    /: time interval added to final sum
    -: time interval not added
    """
    utc_today_midnight = dates_helper.local_to_utc_time(dates_helper.get_midnight(dates_helper.local_now())).replace(
        tzinfo=None
    )
    utc_yday_midnight = dates_helper.day_before(utc_today_midnight)
    latest_settings_before_yesterday = (
        core.models.settings.AdGroupSettings.objects.filter(ad_group_id__in=ad_groups)
        .filter(created_dt__lte=utc_yday_midnight)
        .latest_per_entity()
        .only("ad_group_id", "created_dt", "state")
    )
    all_settings_yesterday = (
        core.models.settings.AdGroupSettings.objects.filter(ad_group_id__in=ad_groups)
        .filter(created_dt__gte=utc_yday_midnight, created_dt__lt=dates_helper.day_after(utc_yday_midnight))
        .only("ad_group_id", "created_dt", "state")
    )
    settings_valid_yesterday_union = latest_settings_before_yesterday.union(all_settings_yesterday).order_by(
        "ad_group_id", "created_dt"
    )

    time_active_per_ad_group_id = defaultdict(int)
    for ad_group_id, ags_group in itertools.groupby(settings_valid_yesterday_union, operator.attrgetter("ad_group_id")):
        for previous_ags, current_ags in _get_lookahead_iter(ags_group):
            if previous_ags.state == dash.constants.AdGroupSettingsState.ACTIVE:
                interval_start = (
                    previous_ags.created_dt if previous_ags.created_dt >= utc_yday_midnight else utc_yday_midnight
                )
                interval_end = current_ags.created_dt if current_ags else utc_today_midnight
                seconds_active = (interval_end - interval_start).total_seconds()
                time_active_per_ad_group_id[ad_group_id] += seconds_active
    return time_active_per_ad_group_id


def _get_lookahead_iter(iterable):
    it1, it2 = itertools.tee(iterable)
    next(it2, None)
    return itertools.zip_longest(it1, it2)
