# Hooks and hacks for Native server

from django.contrib.auth import models as authmodels

import dash.constants

AGENCY_RCS_ID = 220
AGENCY_NEWSCORP_ID = 86
CPC_GOAL_TO_BID_AGENCIES = (AGENCY_RCS_ID, AGENCY_NEWSCORP_ID)
# Non NAS AGENCY
AGENCY_MEDIAMOND_ID = 196
AGENCY_AMMET_ID = 289
AGENCY_ROI_MARKETPLACE_ID = 208
AGENCY_KONTENT_ROOM = 109

AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY = {
    AGENCY_RCS_ID: {
        "target_regions": ["IT"],
        "exclusion_target_regions": [],
        "delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED,
    },
    AGENCY_AMMET_ID: {"target_regions": ["AU"], "exclusion_target_regions": []},
    AGENCY_MEDIAMOND_ID: {"tracking_code": "utm_source=Mediamond&utm_medium=referral"},
    AGENCY_NEWSCORP_ID: {
        "delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED,
        "target_regions": ["AU"],
        "exclusion_target_regions": [],
    },
}
AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY = {
    AGENCY_RCS_ID: {"delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED},
    AGENCY_NEWSCORP_ID: {"delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED},
}

CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY = {
    AGENCY_RCS_ID: {"language": "it", "autopilot": True},
    AGENCY_NEWSCORP_ID: {"language": "en", "autopilot": True},
    AGENCY_ROI_MARKETPLACE_ID: {"iab_category": dash.constants.IABCategory.IAB3_11},
    AGENCY_KONTENT_ROOM: {"iab_category": dash.constants.IABCategory.IAB3_11},
}

CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY = {
    AGENCY_RCS_ID: {"language": "it", "autopilot": True},
    AGENCY_NEWSCORP_ID: {"language": "en", "autopilot": True},
}

FIXED_CAMPAIGN_TYPE_PER_AGENCY = {
    AGENCY_RCS_ID: dash.constants.CampaignType.CONTENT,
    AGENCY_NEWSCORP_ID: dash.constants.CampaignType.CONTENT,
}


def _update_ad_group_sources_cpc(request, ad_group, cpc_cc):
    ad_group.settings.update(request, b1_sources_group_cpc_cc=cpc_cc, skip_validation=True)
    for ad_group_source in ad_group.adgroupsource_set.all().select_related("settings"):
        ad_group_source.settings.update(request, cpc_cc=cpc_cc)


def apply_ad_group_create_hacks(request, ad_group):
    if ad_group.campaign.account.agency_id in AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY:
        ad_group.settings.update(
            request, **AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY[ad_group.campaign.account.agency_id]
        )
    if ad_group.campaign.account.agency_id in CPC_GOAL_TO_BID_AGENCIES:
        goal_cpc_value = _get_cpc_goal_value(ad_group.campaign)
        _update_ad_group_sources_cpc(request, ad_group, goal_cpc_value.value)


def override_ad_group_settings_form_data(ad_group, form_data):
    if ad_group.campaign.account.agency_id in AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY:
        form_data.update(AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY[ad_group.campaign.account.agency_id])
    return form_data


def _get_cpc_goal_value(campaign):
    cpc_goal = campaign.campaigngoal_set.filter(type=dash.constants.CampaignGoalKPI.CPC).first()
    if not cpc_goal:
        raise Exception("No CPC goal on the RCS campaign.")
    return cpc_goal.get_current_value()


def _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data):
    if ad_group.campaign.account.agency_id in CPC_GOAL_TO_BID_AGENCIES:
        cpc_goal_value = _get_cpc_goal_value(ad_group.campaign)
        if form_data.get("local_cpc_cc"):
            form_data["local_cpc_cc"] = cpc_goal_value.local_value
        else:
            form_data["cpc_cc"] = cpc_goal_value.value
    return form_data


def override_ad_group_source_settings_form_data(ad_group, form_data):
    if ad_group.campaign.account.agency_id in CPC_GOAL_TO_BID_AGENCIES:
        return _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data)
    return form_data


def apply_set_goals_hacks(campaign, goal_changes):
    if campaign.account.agency_id in CPC_GOAL_TO_BID_AGENCIES:
        return {
            "added": list(
                filter(lambda goal: goal["type"] == dash.constants.CampaignGoalKPI.CPC, goal_changes["added"])
            ),
            "removed": goal_changes["removed"],
            "primary": goal_changes["primary"],
            "modified": goal_changes["modified"],
        }
    return goal_changes


def apply_create_user_hacks(user, account):
    if account.agency_id == AGENCY_RCS_ID:
        for group in authmodels.Group.objects.filter(name__in=("Public - default for all new accounts",)):
            user.groups.remove(group)
        for group in authmodels.Group.objects.filter(name__in=("NAS - RCS",)):
            user.groups.add(group)
    if account.agency_id == AGENCY_NEWSCORP_ID:
        for group in authmodels.Group.objects.filter(name__in=("Public - default for all new accounts",)):
            user.groups.remove(group)
        for group in authmodels.Group.objects.filter(name__in=("NAS - Newscorp",)):
            user.groups.add(group)


def apply_campaign_create_hacks(request, campaign):
    if campaign.account.agency_id in CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY:
        campaign.settings.update(request, **CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    if campaign.account.agency_id in FIXED_CAMPAIGN_TYPE_PER_AGENCY:
        campaign.update_type(type=FIXED_CAMPAIGN_TYPE_PER_AGENCY[campaign.account.agency_id])


def apply_campaign_change_hacks(request, campaign, goal_changes):
    if campaign.account.agency_id in CPC_GOAL_TO_BID_AGENCIES:
        if not (goal_changes["modified"] or goal_changes["added"]):
            return
        for ad_group in campaign.adgroup_set.all():
            _update_ad_group_sources_cpc(request, ad_group, _get_cpc_goal_value(ad_group.campaign).value)


def override_campaign_settings_form_data(campaign, form_data):
    if campaign.account.agency_id in CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY:
        form_data.update(CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    return form_data
