from dash import models
from dash import constants


def get_ad_group_dict(ad_group, ad_group_settings, ad_group_source_settings, include_archived_flag):

    running_status = models.AdGroup.get_running_status(ad_group_settings, ad_group_source_settings)
    state = ad_group_settings.state if ad_group_settings else constants.AdGroupSettingsState.INACTIVE

    ad_group_dict = {
        'id': ad_group.id,
        'name': ad_group.name,
        'contentAdsTabWithCMS': ad_group.content_ads_tab_with_cms,
        'status': constants.AdGroupRunningStatus.get_text(running_status).lower(),
        'state': constants.AdGroupSettingsState.get_text(state).lower()
    }
    if include_archived_flag:
        ad_group_dict['archived'] = ad_group_settings.archived if ad_group_settings else False

    return ad_group_dict


def get_campaign_dict(campaign, campaign_settings=None, include_archived_flag=False):

    campaign_dict = {
        'id': campaign.id,
        'name': campaign.name
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
