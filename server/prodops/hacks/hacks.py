# Hooks and hacks for Native server

from django.contrib.auth import models as authmodels

import dash.constants

from . import constants

######################
# AdGroupSource hacks
######################


def override_ad_group_source_settings_form_data(ad_group, form_data):
    if ad_group.campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        return _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data)
    return form_data


######################
# AdGroup hacks
######################


def apply_ad_group_create_hacks(request, ad_group):
    if ad_group.campaign.account.agency_id in constants.AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY:
        data = constants.AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY[ad_group.campaign.account.agency_id]
        if ad_group.campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
            goal_cpc_value = _get_cpc_goal_value(ad_group.campaign)
            data.update({"b1_sources_group_cpc_cc": goal_cpc_value.value})
            _update_ad_group_sources_cpc(request, ad_group, goal_cpc_value.value)
        ad_group.settings.update(request, skip_validation=True, **data)


def override_ad_group_settings(ad_group, updates):
    if ad_group.campaign.account.agency_id in constants.AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY:
        updates.update(constants.AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY[ad_group.campaign.account.agency_id])
    return updates


######################
# Campaign hacks
######################


def apply_campaign_create_hacks(request, campaign):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY:
        campaign.settings.update(
            request, **constants.CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY[campaign.account.agency_id]
        )
    if campaign.account.agency_id in constants.FIXED_CAMPAIGN_TYPE_PER_AGENCY:
        campaign.update_type(type=constants.FIXED_CAMPAIGN_TYPE_PER_AGENCY[campaign.account.agency_id])


def apply_campaign_change_hacks_form_data(request, campaign, goal_changes):
    if campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        if not (goal_changes["modified"] or goal_changes["added"]):
            return
        _apply_goal_bid_cpc(request, campaign)


def apply_campaign_goals_change_hacks(request, campaign):
    if campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        _apply_goal_bid_cpc(request, campaign)


def filter_campaign_goals_form_data(campaign, goal_changes):
    if campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        return {
            "added": list(
                filter(lambda goal: goal["type"] == dash.constants.CampaignGoalKPI.CPC, goal_changes["added"])
            ),
            "removed": goal_changes["removed"],
            "primary": goal_changes["primary"],
            "modified": goal_changes["modified"],
        }
    return goal_changes


def filter_campaign_goals(campaign, goals):
    if campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        return list(filter(lambda goal: goal["type"] == dash.constants.CampaignGoalKPI.CPC, goals))
    return goals


def override_campaign_settings_form_data(campaign, form_data):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY:
        form_data.update(constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    return form_data


def override_campaign_settings(campaign, updates):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY:
        updates.update(constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    return updates


######################
# User hacks
######################


def apply_create_user_hacks(user, agency):
    if agency and agency.id == constants.AGENCY_RCS_ID:
        for group in authmodels.Group.objects.filter(name__in=("NAS - RCS",)):
            user.groups.add(group)
        return
    if agency and agency.id == constants.AGENCY_NEWSCORP_ID:
        for group in authmodels.Group.objects.filter(name__in=("NAS - Newscorp",)):
            user.groups.add(group)


######################
# Account hacks
######################
def apply_account_create_hack(request, account):
    if account.agency_id == constants.AGENCY_QOOL_MEDIA:
        account_cf = account.custom_flags or dict()
        account_cf.update({constants.MSN_BLOCK_CF_ID: True})
        account.update(request, custom_flags=account_cf)


######################
# Private functions
######################


def _update_ad_group_sources_cpc(request, ad_group, cpc_cc):
    for ad_group_source in ad_group.adgroupsource_set.all().select_related("settings"):
        ad_group_source.settings.update(request, cpc_cc=cpc_cc)


def _get_cpc_goal_value(campaign):
    cpc_goal = campaign.campaigngoal_set.filter(type=dash.constants.CampaignGoalKPI.CPC).first()
    if not cpc_goal:
        raise Exception("No CPC goal on the RCS campaign.")
    return cpc_goal.get_current_value()


def _apply_goal_bid_cpc(request, campaign):
    new_cpc = _get_cpc_goal_value(campaign).value
    for ad_group in campaign.adgroup_set.all():
        ad_group.settings.update(request, skip_validation=True, b1_sources_group_cpc_cc=new_cpc)
        _update_ad_group_sources_cpc(request, ad_group, new_cpc)


def _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data):
    if ad_group.campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        cpc_goal_value = _get_cpc_goal_value(ad_group.campaign)
        if form_data.get("local_cpc_cc"):
            form_data["local_cpc_cc"] = cpc_goal_value.local_value
        else:
            form_data["cpc_cc"] = cpc_goal_value.value
    return form_data
