from .. import constants, CampaignStopState
from utils import dates_helper


def get_campaignstop_state(campaign):
    return get_campaignstop_states([campaign])[campaign.id]


def get_campaignstop_states(campaigns):
    states_map = _get_states_map(campaigns)
    return {
        campaign.id: _get_campaign_stop_state(campaign, states_map) for campaign in campaigns
    }


def _get_states_map(campaigns):
    return {
        st.campaign_id: st for st in CampaignStopState.objects.filter(campaign__in=campaigns)
    }


def _get_campaign_stop_state(campaign, states_map):
    max_allowed_end_date = _get_max_allowed_end_date(campaign, states_map)
    return {
        'allowed_to_run': _is_allowed_to_run(campaign, states_map, max_allowed_end_date),
        'max_allowed_end_date': max_allowed_end_date,
        'almost_depleted': _is_almost_depleted(campaign, states_map),
        'pending_budget_updates': _is_pending_budget_updates(campaign, states_map),
    }


def _is_allowed_to_run(campaign, states_map, max_allowed_end_date):
    if not campaign.real_time_campaign_stop:
        return True

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
    return campaignstop_state.state == constants.CampaignStopState.STOPPED and\
        campaignstop_state.pending_budget_updates
