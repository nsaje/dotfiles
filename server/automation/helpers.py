import dash
from dash.views import helpers
import reports.api


def get_yesterdays_spends(campaigns):
    return {campaign.id:
            sum(reports.api.get_yesterday_cost(campaign=campaign).values())
            for campaign in campaigns}


def get_available_budgets(campaigns):
    total_budgets = _get_total_budgets(campaigns)
    total_spends = _get_total_spends(campaigns)
    return {k: float(total_budgets[k]) - float(total_spends[k])
            for k in total_budgets if k in total_spends}


def _get_total_budgets(campaigns):
    return {campaign.id: dash.budget.CampaignBudget(campaign).get_total()
            for campaign in campaigns}


def _get_total_spends(campaigns):
    return {campaign.id: dash.budget.CampaignBudget(campaign).get_spend()
            for campaign in campaigns}


def get_active_campaigns():
    return _get_active_campaigns_subset(dash.models.Campaign.objects.all())


def _get_active_campaigns_subset(campaigns):
    for campaign in campaigns:
        adgroups = dash.models.AdGroup.objects.filter(campaign=campaign)
        is_active = False
        for adgroup in adgroups:
            adgroup_settings = adgroup.get_current_settings()
            if adgroup_settings.state == dash.constants.AdGroupSettingsState.ACTIVE and \
                    not adgroup_settings.archived and \
                    not adgroup.is_demo:
                is_active = True
                break
        if not is_active:
            campaigns = campaigns.exclude(pk=campaign.pk)
    return campaigns


def get_autopilot_ad_group_sources_settings(adgroup):
    autopilot_sources_settings = []
    all_ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=adgroup)
    for current_source_settings in dash.views.helpers.get_ad_group_sources_settings(all_ad_group_sources):
        if (current_source_settings.state == dash.constants.AdGroupSourceSettingsState.ACTIVE and
                current_source_settings.autopilot):
            autopilot_sources_settings.append(current_source_settings)
    return autopilot_sources_settings


def get_active_ad_groups(campaign):
    active_ad_groups = []
    adgroups = campaign.adgroup_set.all()
    for adg in adgroups:
        adgroup_settings = adg.get_current_settings()
        if adgroup_settings.state == dash.constants.AdGroupSettingsState.ACTIVE and \
                not adgroup_settings.archived and \
                not adg.is_demo:
            active_ad_groups.append(adg)
    return active_ad_groups
