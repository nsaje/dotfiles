from dash import models
from dash import constants


def map_ad_group_sources_settings(ad_groups_sources_settings, map_ad_group_source):
    map_ad_groups_sources_settings = {}
    for ad_group_source_settings in ad_groups_sources_settings:
        ad_group_source_id = ad_group_source_settings.ad_group_source_id

        # filter by ad group and source
        if ad_group_source_id in map_ad_group_source:
            ad_group_id = map_ad_group_source[ad_group_source_id]
            map_ad_groups_sources_settings.setdefault(ad_group_id, []).append(ad_group_source_settings)
    return map_ad_groups_sources_settings


def get_ad_group_dict(ad_group, ad_group_settings, ad_group_source_settings, include_archived_flag):

    running_status = models.AdGroup.get_running_status(ad_group_settings, ad_group_source_settings)
    state = ad_group_settings.state if ad_group_settings else constants.AdGroupSettingsState.INACTIVE

    ad_group_dict = {
        'id': ad_group.id,
        'name': ad_group.name,
        'contentAdsTabWithCMS': ad_group.content_ads_tab_with_cms,
        'status': running_status,
        'state': state
    }
    if include_archived_flag:
        ad_group_dict['archived'] = ad_group_settings.archived if ad_group_settings else False

    return ad_group_dict


def get_campaign_dict(campaign, campaign_settings=None, include_archived_flag=False):

    campaign_dict = {
        'id': campaign.id,
        'name': campaign.name,
        'landingMode': campaign.is_in_landing(),
    }

    if include_archived_flag:
        campaign_settings = campaign_settings
        campaign_dict['archived'] = campaign_settings.archived if campaign_settings else False

    return campaign_dict


def get_account_dict(account, account_settings=None, include_archived_flag=False):
    account_dict = {
        'id': account.id,
        'name': account.name,
    }

    if include_archived_flag:
        account_settings = account_settings
        account_dict['archived'] = account_settings.archived if account_settings else False

    return account_dict
