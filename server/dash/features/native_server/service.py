# Hooks and hacks for Native server

from django.contrib.auth import models as authmodels

import dash.constants


AGENCY_RCS = 220
AGENCY_MEDIAMOND = 196

AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY = {AGENCY_RCS: {"target_regions": [], "exclusion_target_regions": []}}
AD_GROUP_SETTINGS_HACKS_PER_AGENCY = {AGENCY_RCS: {"delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED}}
CAMPAIGN_SETTINGS_HACKS_PER_AGENCY = {AGENCY_RCS: {"language": "it", "autopilot": True}}


def _update_ad_group_sources_cpc(request, ad_group, cpc_cc):
    for ad_group_source in ad_group.adgroupsource_set.all().select_related("settings"):
        ad_group_source.settings.update(request, cpc_cc=cpc_cc)


def apply_ad_group_create_hacks(request, ad_group):
    if ad_group.campaign.account.agency_id in AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY:
        ad_group.settings.update(
            request, **AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY[ad_group.campaign.account.agency_id]
        )
        _update_ad_group_sources_cpc(request, ad_group, _get_cpc_goal_value(ad_group.campaign).value)
    if ad_group.campaign.account.agency_id == AGENCY_MEDIAMOND:
        ad_group.settings.update(request, tracking_code="utm_source=Zemanta&utm_medium=referral")


def transform_ad_group_settings(ad_group, form_data):
    if ad_group.campaign.account.agency_id in AD_GROUP_SETTINGS_HACKS_PER_AGENCY:
        form_data.update(AD_GROUP_SETTINGS_HACKS_PER_AGENCY[ad_group.campaign.account.agency_id])
    return form_data


def _get_cpc_goal_value(campaign):
    cpc_goal = campaign.campaigngoal_set.filter(type=dash.constants.CampaignGoalKPI.CPC).first()
    return cpc_goal.get_current_value()


def _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data):
    if ad_group.campaign.account.agency_id == AGENCY_RCS:
        cpc_goal_value = _get_cpc_goal_value(ad_group.campaign)
        if form_data.get("local_cpc_cc"):
            form_data["local_cpc_cc"] = cpc_goal_value.local_value
        else:
            form_data["cpc_cc"] = cpc_goal_value.value
    return form_data


def transform_ad_group_source_settings(ad_group, form_data):
    if ad_group.campaign.account.agency_id == AGENCY_RCS:
        return _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data)
    return form_data


def apply_set_goals_hacks(campaign, goal_changes):
    if campaign.account.agency_id == AGENCY_RCS:
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
    if account.agency_id == AGENCY_RCS:
        for group in authmodels.Group.objects.filter(name__in=("Public - default for all new accounts",)):
            user.groups.remove(group)
        for group in authmodels.Group.objects.filter(name__in=("NAS - RCS",)):
            user.groups.add(group)


def apply_campaign_create_hacks(request, campaign):
    if campaign.account.agency_id in CAMPAIGN_SETTINGS_HACKS_PER_AGENCY:
        campaign.settings.update(request, **CAMPAIGN_SETTINGS_HACKS_PER_AGENCY[campaign.account.agency_id])


def apply_campaign_change_hacks(request, campaign, goal_changes):
    if campaign.account.agency_id == AGENCY_RCS:
        if not (goal_changes["modified"] or goal_changes["added"]):
            return
        for ad_group in campaign.adgroup_set.all():
            _update_ad_group_sources_cpc(request, ad_group, _get_cpc_goal_value(ad_group.campaign).value)


def transform_campaign_settings(campaign, form_data):
    if campaign.account.agency_id in CAMPAIGN_SETTINGS_HACKS_PER_AGENCY:
        form_data.update(CAMPAIGN_SETTINGS_HACKS_PER_AGENCY[campaign.account.agency_id])
    return form_data
