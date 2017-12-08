from .. import constants, CampaignStopState


def get_campaignstop_states(campaigns):
    states_map = _get_states_map(campaigns)
    return {
        campaign: _is_allowed_to_run(campaign, states_map) for campaign in campaigns
    }


def _get_states_map(campaigns):
    return {
        st.campaign_id: st.state for st in CampaignStopState.objects.filter(campaign__in=campaigns)
    }


def _is_allowed_to_run(campaign, states_map):
    if not campaign.real_time_campaign_stop:
        return True

    state = states_map.get(campaign.id, constants.CampaignStopState.STOPPED)
    return state == constants.CampaignStopState.ACTIVE
