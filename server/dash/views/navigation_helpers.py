from dash import models
from dash import constants
from dash import infobox_helpers


def get_ad_group_dict(
    user,
    ad_group,
    ad_group_settings,
    campaign_settings,
    campaignstop_state,
    real_time_campaign_stop=False,
    with_settings=True,
):
    if not with_settings:
        return {"id": ad_group["id"], "name": ad_group["name"]}

    running_status = models.AdGroup.get_running_status(ad_group_settings)
    state = ad_group_settings.state if ad_group_settings else constants.AdGroupSettingsState.INACTIVE
    is_campaign_autopilot = campaign_settings.autopilot if campaign_settings else False
    autopilot_state = (
        ad_group_settings.autopilot_state if ad_group_settings else constants.AdGroupSettingsAutopilotState.INACTIVE
    )
    ad_group_dict = {
        "id": ad_group["id"],
        "name": ad_group["name"],
        "status": running_status,
        "state": state,
        "archived": ad_group_settings.archived if ad_group_settings else False,
        "autopilot_state": autopilot_state,
        "bidding_type": ad_group["bidding_type"],
        "active": infobox_helpers.get_adgroup_running_status_class(
            user,
            autopilot_state,
            running_status,
            state,
            real_time_campaign_stop,
            campaignstop_state,
            is_campaign_autopilot,
        ),
    }
    return ad_group_dict


def get_campaign_dict(campaign, campaign_settings, with_settings=True):
    if not with_settings:
        return {"id": campaign["id"], "name": campaign["name"], "type": campaign["type"]}

    campaign_dict = {
        "id": campaign["id"],
        "name": campaign["name"],
        "archived": campaign_settings.archived if campaign_settings else False,
        "type": campaign["type"],
    }
    return campaign_dict


def get_account_dict(account, account_settings=None, with_settings=True):
    if not with_settings:
        return {
            "id": account["id"],
            "name": account["name"],
            "agency": account["agency__name"],
            "currency": account["currency"],
            "usesBCMv2": account["uses_bcm_v2"],
        }

    account_dict = {
        "id": account["id"],
        "name": account["name"],
        "archived": account_settings.archived if account_settings else False,
        "agency": account["agency__name"],
        "currency": account["currency"],
        "usesBCMv2": account["uses_bcm_v2"],
    }
    return account_dict
