import collections
from typing import Dict
from typing import Iterable

import automation.campaignstop
import core.models
import dash.constants

from . import models


def get_accounts_statuses_cached(account_ids: Iterable[int]) -> Dict[int, int]:
    status_map: Dict[int, int] = collections.defaultdict(lambda: dash.constants.AdGroupRunningStatus.INACTIVE)
    status_map.update(
        {
            r["account_id"]: r["status"]
            for r in models.AccountStatusCache.objects.filter(account_id__in=account_ids).values()
        }
    )
    return status_map


def refresh_accounts_statuses_cache():
    account_ids = core.models.Account.objects.exclude_archived().values_list("id", flat=True)
    new_statuses = get_accounts_statuses(account_ids)
    active_ids = {
        acc_id for acc_id, status in new_statuses.items() if status == dash.constants.AdGroupRunningStatus.ACTIVE
    }
    _ensure_cache_objects_exist(active_ids)
    models.AccountStatusCache.objects.filter(account_id__in=active_ids).filter(
        status=dash.constants.AdGroupRunningStatus.INACTIVE
    ).update(status=dash.constants.AdGroupRunningStatus.ACTIVE)
    models.AccountStatusCache.objects.exclude(account_id__in=active_ids).filter(
        status=dash.constants.AdGroupRunningStatus.ACTIVE
    ).update(status=dash.constants.AdGroupRunningStatus.INACTIVE)


def _ensure_cache_objects_exist(account_ids: Iterable[int]):
    existing_ids = models.AccountStatusCache.objects.all().values_list("account_id", flat=True)
    missing_ids = set(account_ids) - set(existing_ids)
    missing_objs = [models.AccountStatusCache(account_id=acc_id) for acc_id in missing_ids]
    models.AccountStatusCache.objects.bulk_create(missing_objs)


def get_accounts_statuses(account_ids: Iterable[int]) -> Dict[int, int]:
    account_ids_state = (
        core.models.AdGroup.objects.filter(
            campaign__account_id__in=account_ids, settings__state=dash.constants.AdGroupRunningStatus.ACTIVE
        )
        .values_list("campaign_id", "campaign__account_id")
        .distinct()
        .order_by()
    )  # removes default ordering to speed up the query
    campaignstop_states = automation.campaignstop.get_campaignstop_states(
        core.models.Campaign.objects.filter(account_id__in=account_ids)
    )

    status_map: Dict[int, int] = collections.defaultdict(lambda: dash.constants.AdGroupRunningStatus.INACTIVE)
    for campaign_id, account_id in account_ids_state:
        if campaignstop_states.get(campaign_id, {}).get("allowed_to_run", False):
            status_map[account_id] = dash.constants.AdGroupRunningStatus.ACTIVE

    return status_map
