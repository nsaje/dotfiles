import concurrent.futures
import decimal
from functools import partial
from threading import Lock
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from django.db import transaction

import core.models
from utils import dates_helper
from utils import zlogging

from .. import CampaignStopState
from .. import RealTimeCampaignStopLog
from .. import constants
from . import config
from . import refresh_realtime_data
from . import spends_helper

logger = zlogging.getLogger(__name__)


def update_campaigns_state(campaigns: Optional[List[core.models.Campaign]] = None) -> None:
    campaigns_list = _get_campaigns(campaigns)
    _process_campaigns(campaign for campaign in campaigns_list if campaign.real_time_campaign_stop)


def _get_campaigns(campaigns: Optional[List[core.models.Campaign]] = None) -> Iterable[core.models.Campaign]:
    if campaigns:
        return campaigns
    return core.models.Campaign.objects.filter(real_time_campaign_stop=True)


def _process_campaigns(campaigns: Iterable[core.models.Campaign]) -> None:
    with concurrent.futures.ProcessPoolExecutor(max_workers=config.JOB_PARALLELISM) as executor:
        executor.map(
            partial(_process_campaign_thread_logging_wrapper, Lock(), {"total": len(campaigns), "current": 0}),
            campaigns,
        )


def _process_campaign_thread_logging_wrapper(
    lock: Lock, shared: Dict[str, int], campaign: core.models.Campaign
) -> None:
    _process_campaign(campaign)
    with lock:
        shared["current"] += 1
        logger.info(
            "Finished processing campaign {campaign_id} ({current}/{total})".format(
                campaign_id=campaign.id, current=shared["current"], total=shared["total"]
            )
        )


def _process_campaign(campaign: core.models.Campaign) -> None:
    refresh_realtime_data([campaign])
    _update_campaign(campaign)


@transaction.atomic
def _update_campaign(campaign: core.models.Campaign) -> None:
    campaign_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)

    log = RealTimeCampaignStopLog(campaign=campaign, event=constants.CampaignStopEvent.BUDGET_DEPLETION_CHECK)

    log.add_context({"previous_state": campaign_state.state})
    allowed_to_run = _is_allowed_to_run(log, campaign, campaign_state)
    campaign_state.set_allowed_to_run(allowed_to_run)
    if not allowed_to_run:
        campaign_state.update_almost_depleted(False)
    log.add_context({"new_state": campaign_state.state})


def _is_allowed_to_run(
    log: RealTimeCampaignStopLog, campaign: core.models.Campaign, campaign_state: CampaignStopState
) -> bool:
    allowed_to_run = not _is_max_end_date_past(log, campaign, campaign_state) and not _is_below_threshold(
        log, campaign, campaign_state
    )
    log.add_context({"allowed_to_run": allowed_to_run})
    return allowed_to_run


def _is_max_end_date_past(
    log: RealTimeCampaignStopLog, campaign: core.models.Campaign, campaign_state: CampaignStopState
) -> Optional[bool]:
    is_past = campaign_state.max_allowed_end_date and campaign_state.max_allowed_end_date < dates_helper.local_today()
    log.add_context({"max_allowed_end_date": campaign_state.max_allowed_end_date, "is_max_end_date_past": is_past})
    return is_past


def _is_below_threshold(
    log: RealTimeCampaignStopLog, campaign: core.models.Campaign, campaign_state: CampaignStopState
) -> bool:
    predicted = spends_helper.get_predicted_remaining_budget(log, campaign)
    threshold = _get_threshold(campaign_state)
    is_below = predicted < threshold
    log.add_context({"predicted": predicted, "is_below_threshold": is_below, "threshold": threshold})
    return is_below


def _get_threshold(campaign_state: CampaignStopState) -> decimal.Decimal:
    if campaign_state.state == constants.CampaignStopState.STOPPED:
        # NOTE: avoid restarting when a stopped campaign only slightly above threshold is checked
        return config.THRESHOLD * decimal.Decimal("1.5")
    return decimal.Decimal(config.THRESHOLD)
