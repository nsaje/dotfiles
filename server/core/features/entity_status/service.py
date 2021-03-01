import collections
import decimal
from typing import Dict
from typing import Iterable
from typing import Union

from django.db.models import F
from django.db.models import Sum

import automation.campaignstop
import core.models
import dash.constants

from . import models


def get_accounts_statuses_cached(account_ids: Iterable[int]) -> Dict[int, Dict[str, Union[int, decimal.Decimal]]]:
    status_map: Dict[int, Dict[str, Union[int, decimal.Decimal]]] = collections.defaultdict(
        lambda: {"status": dash.constants.AdGroupRunningStatus.INACTIVE, "local_daily_budget": decimal.Decimal("0")}
    )
    status_map.update(
        {
            r["account_id"]: {
                "status": r["status"],
                "local_daily_budget": r["local_daily_budget"],
            }
            for r in models.AccountStatusCache.objects.filter(account_id__in=account_ids).values()
        }
    )
    return status_map


def refresh_accounts_cache():
    account_ids = core.models.Account.objects.exclude_archived().values_list("id", flat=True)
    new_statuses = _get_accounts_statuses(account_ids)
    active_ids = {
        acc_id for acc_id, status in new_statuses.items() if status == dash.constants.AdGroupRunningStatus.ACTIVE
    }
    local_daily_budgets = _get_local_daily_budgets(active_ids)
    _ensure_cache_objects_exist(active_ids)
    models.AccountStatusCache.objects.exclude(account_id__in=active_ids).filter(
        status=dash.constants.AdGroupRunningStatus.ACTIVE
    ).update(status=dash.constants.AdGroupRunningStatus.INACTIVE, local_daily_budget=decimal.Decimal(0))
    for active_id in active_ids:
        models.AccountStatusCache.objects.filter(account_id=active_id).update(
            status=dash.constants.AdGroupRunningStatus.ACTIVE,
            local_daily_budget=local_daily_budgets.get(active_id, decimal.Decimal(0)),
        )


def _ensure_cache_objects_exist(account_ids: Iterable[int]):
    existing_ids = models.AccountStatusCache.objects.all().values_list("account_id", flat=True)
    missing_ids = set(account_ids) - set(existing_ids)
    missing_objs = [models.AccountStatusCache(account_id=acc_id) for acc_id in missing_ids]
    models.AccountStatusCache.objects.bulk_create(missing_objs)


def _get_accounts_statuses(account_ids: Iterable[int]) -> Dict[int, int]:
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


def _get_local_daily_budgets(account_ids):
    qs = (
        core.models.AdGroup.objects.filter(campaign__account_id__in=account_ids)
        .filter_running()
        .order_by()
        .values("campaign__account_id")
        .annotate(account_id=F("campaign__account_id"), local_daily_budget=Sum("settings__local_daily_budget"))
        .values("account_id", "local_daily_budget")
    )
    local_daily_budgets_map: Dict[int, decimal.Decimal] = {row["account_id"]: row["local_daily_budget"] for row in qs}
    return local_daily_budgets_map
