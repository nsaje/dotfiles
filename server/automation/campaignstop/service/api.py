from .. import constants, CampaignStopState


def get_campaignstop_states(campaigns):
    states_map = _get_states_map(campaigns)
    return {
        campaign: _is_allowed_to_run(campaign, states_map) for campaign in campaigns
    }


def get_max_end_dates(campaigns):
    states_map = _get_states_map(campaigns)

    return {
        campaign: _get_max_allowed_end_date(campaign, states_map) for campaign in campaigns
    }


def _get_states_map(campaigns):
    return {
        st.campaign_id: st for st in CampaignStopState.objects.filter(campaign__in=campaigns)
    }


def _get_max_allowed_end_date(campaign, states_map):
    if not campaign.real_time_campaign_stop or campaign.id not in states_map:
        return None

    return states_map[campaign.id].max_allowed_end_date


def _is_allowed_to_run(campaign, states_map):
    if not campaign.real_time_campaign_stop:
        return True

    campaignstop_state = states_map.get(campaign.id)
    if not campaignstop_state:
        return False

    return campaignstop_state.state == constants.CampaignStopState.ACTIVE
