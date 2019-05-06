# Hooks and hacks for Native server

from django.contrib.auth import models as authmodels

import core.models
import dash.constants
import dash.features.whitelabels
import serviceapi.salesforce.constants
from zemauth.models import User

from . import constants


def _update_ad_group_sources_cpc(request, ad_group, cpc_cc):
    ad_group.settings.update(request, b1_sources_group_cpc_cc=cpc_cc, skip_validation=True)
    for ad_group_source in ad_group.adgroupsource_set.all().select_related("settings"):
        ad_group_source.settings.update(request, cpc_cc=cpc_cc)


def apply_ad_group_create_hacks(request, ad_group):
    if ad_group.campaign.account.agency_id in constants.AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY:
        ad_group.settings.update(
            request, **constants.AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY[ad_group.campaign.account.agency_id]
        )
    if ad_group.campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        goal_cpc_value = _get_cpc_goal_value(ad_group.campaign)
        _update_ad_group_sources_cpc(request, ad_group, goal_cpc_value.value)


def override_ad_group_settings_form_data(ad_group, form_data):
    if ad_group.campaign.account.agency_id in constants.AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY:
        form_data.update(constants.AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY[ad_group.campaign.account.agency_id])
    return form_data


def _get_cpc_goal_value(campaign):
    cpc_goal = campaign.campaigngoal_set.filter(type=dash.constants.CampaignGoalKPI.CPC).first()
    if not cpc_goal:
        raise Exception("No CPC goal on the RCS campaign.")
    return cpc_goal.get_current_value()


def _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data):
    if ad_group.campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        cpc_goal_value = _get_cpc_goal_value(ad_group.campaign)
        if form_data.get("local_cpc_cc"):
            form_data["local_cpc_cc"] = cpc_goal_value.local_value
        else:
            form_data["cpc_cc"] = cpc_goal_value.value
    return form_data


def override_ad_group_source_settings_form_data(ad_group, form_data):
    if ad_group.campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        return _transform_bid_cpc_value_from_campaign_goal(ad_group, form_data)
    return form_data


def apply_set_goals_hacks(campaign, goal_changes):
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


def apply_create_user_hacks(user, account):
    if account.agency_id == constants.AGENCY_RCS_ID:
        for group in authmodels.Group.objects.filter(name__in=("Public - default for all new accounts",)):
            user.groups.remove(group)
        for group in authmodels.Group.objects.filter(name__in=("NAS - RCS",)):
            user.groups.add(group)
    if account.agency_id == constants.AGENCY_NEWSCORP_ID:
        for group in authmodels.Group.objects.filter(name__in=("Public - default for all new accounts",)):
            user.groups.remove(group)
        for group in authmodels.Group.objects.filter(name__in=("NAS - Newscorp",)):
            user.groups.add(group)
    if (
        account.is_agency()
        and account.agency.entity_tags.filter(name=serviceapi.salesforce.constants.MANAGED_BY_AMPLIFY_TAG).exists()
    ):
        amplify_group = authmodels.Group.objects.get(
            permissions__codename=serviceapi.salesforce.constants.AMPLIFY_GROUP_PERMISSION_CODENAME
        )
        user.groups.add(amplify_group)

        for ag in core.models.Agency.objects.filter(entity_tags=serviceapi.salesforce.constants.MANAGED_BY_AMPLIFY_TAG):
            ag.users.add(user)


def apply_campaign_create_hacks(request, campaign):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY:
        campaign.settings.update(
            request, **constants.CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY[campaign.account.agency_id]
        )
    if campaign.account.agency_id in constants.FIXED_CAMPAIGN_TYPE_PER_AGENCY:
        campaign.update_type(type=constants.FIXED_CAMPAIGN_TYPE_PER_AGENCY[campaign.account.agency_id])


def apply_campaign_change_hacks(request, campaign, goal_changes):
    if campaign.account.agency_id in constants.CPC_GOAL_TO_BID_AGENCIES:
        if not (goal_changes["modified"] or goal_changes["added"]):
            return
        for ad_group in campaign.adgroup_set.all():
            _update_ad_group_sources_cpc(request, ad_group, _get_cpc_goal_value(ad_group.campaign).value)


def override_campaign_settings_form_data(campaign, form_data):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY:
        form_data.update(constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    return form_data


def add_agency_default_amplify_settings(user, settings):
    if user.has_perm("zemauth.{}".format(serviceapi.salesforce.constants.AMPLIFY_GROUP_PERMISSION_CODENAME)):
        settings.update(
            {
                "white_label": dash.features.whitelabels.WhiteLabel.objects.get(
                    theme=dash.constants.Whitelabel.AMPLIFY
                ),
                "default_account_type": dash.constants.AccountType.MANAGED,
                "entity_tags": [serviceapi.salesforce.constants.MANAGED_BY_AMPLIFY_TAG],
                "users": User.objects.filter(
                    groups__permissions__codename=serviceapi.salesforce.constants.AMPLIFY_GROUP_PERMISSION_CODENAME
                ),
                "allowed_sources": core.models.Source.objects.filter(
                    bidder_slug__in=serviceapi.salesforce.constants.AMPLIFY_SOURCES_SLUG
                ),
            }
        )
        return settings


def filter_amplify_agencies(user, response):
    if user.has_perm("zemauth.{}".format(serviceapi.salesforce.constants.AMPLIFY_GROUP_PERMISSION_CODENAME)):
        response["agencies"] = list(
            core.models.Agency.objects.filter(
                entity_tags=serviceapi.salesforce.constants.MANAGED_BY_AMPLIFY_TAG
            ).values("name", "sales_representative", "cs_representative", "ob_representative", "default_account_type")
        )
