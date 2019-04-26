import newrelic.agent

from utils import dates_helper

from .. import CampaignStopState
from .. import constants


def get_campaignstop_state(campaign):
    return get_campaignstop_states([campaign])[campaign.id]


@newrelic.agent.function_trace()
def get_campaignstop_states(campaigns):
    states_map = _get_states_map(campaigns)
    return {campaign.id: _get_campaign_stop_state(campaign, states_map) for campaign in campaigns}


def _get_states_map(campaigns):
    return {st.campaign_id: st for st in CampaignStopState.objects.filter(campaign__in=campaigns)}


def _get_campaign_stop_state(campaign, states_map):
    max_allowed_end_date = _get_max_allowed_end_date(campaign, states_map)
    min_allowed_start_date = _get_min_allowed_start_date(campaign, states_map)
    return {
        "allowed_to_run": _is_allowed_to_run(campaign, states_map, max_allowed_end_date, min_allowed_start_date),
        "max_allowed_end_date": max_allowed_end_date,
        "min_allowed_start_date": min_allowed_start_date,
        "almost_depleted": _is_almost_depleted(campaign, states_map),
        "pending_budget_updates": _is_pending_budget_updates(campaign, states_map),
    }


def _is_allowed_to_run(campaign, states_map, max_allowed_end_date, min_allowed_start_date):
    if not campaign.real_time_campaign_stop:
        return True

    if min_allowed_start_date is None:
        return False

    if max_allowed_end_date < dates_helper.local_today():
        return False

    campaignstop_state = states_map.get(campaign.id)
    if not campaignstop_state:
        return False

    return campaignstop_state.state == constants.CampaignStopState.ACTIVE


def _get_max_allowed_end_date(campaign, states_map):
    if not campaign.real_time_campaign_stop:
        return None

    campaignstop_state = states_map.get(campaign.id)
    if not campaignstop_state or not campaignstop_state.max_allowed_end_date:
        return dates_helper.day_before(dates_helper.utc_to_local(campaign.created_dt).date())

    return campaignstop_state.max_allowed_end_date


def _get_min_allowed_start_date(campaign, states_map):
    if not campaign.real_time_campaign_stop:
        return None

    campaignstop_state = states_map.get(campaign.id)
    if not campaignstop_state:
        return None

    return campaignstop_state.min_allowed_start_date


def _is_almost_depleted(campaign, states_map):
    if not campaign.real_time_campaign_stop:
        return False

    campaignstop_state = states_map.get(campaign.id)
    if not campaignstop_state:
        return False
    return campaignstop_state.almost_depleted


def _is_pending_budget_updates(campaign, states_map):
    if not campaign.real_time_campaign_stop:
        return False

    campaignstop_state = states_map.get(campaign.id)
    if not campaignstop_state:
        return False
    return campaignstop_state.state == constants.CampaignStopState.STOPPED and campaignstop_state.pending_budget_updates
