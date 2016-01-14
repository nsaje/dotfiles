from dash import constants

from django.db.models import Q


def get_useractiontype(level):
    if level == constants.PublisherBlacklistLevel.GLOBAL:
        return constants.UserActionType.SET_GLOBAL_PUBLISHER_BLACKLIST
    elif level == constants.PublisherBlacklistLevel.ACCOUNT:
        return constants.UserActionType.SET_ACCOUNT_PUBLISHER_BLACKLIST
    elif level == constants.PublisherBlacklistLevel.CAMPAIGN:
        return constants.UserActionType.SET_CAMPAIGN_PUBLISHER_BLACKLIST
    elif level == constants.PublisherBlacklistLevel.ADGROUP:
        return constants.UserActionType.SET_ADGROUP_PUBLISHER_BLACKLIST

    # dev error
    raise Exception('Invalid level')


def get_key(ad_group, level):
    if level == constants.PublisherBlacklistLevel.GLOBAL:
        return True

    if level == constants.PublisherBlacklistLevel.ACCOUNT:
        return ad_group.campaign.account

    if level == constants.PublisherBlacklistLevel.CAMPAIGN:
        return ad_group.campaign

    if level == constants.PublisherBlacklistLevel.ADGROUP:
        return ad_group

    # dev error
    raise Exception('Invalid level')


def create_queryset_by_key(ad_group, level):
    blacklist_account = None
    blacklist_campaign = None
    blacklist_adgroup = None

    blacklist_global = level == constants.PublisherBlacklistLevel.GLOBAL
    if level == constants.PublisherBlacklistLevel.ACCOUNT:
        blacklist_account = ad_group.campaign.account
    if level == constants.PublisherBlacklistLevel.CAMPAIGN:
        blacklist_campaign = ad_group.campaign
    if level == constants.PublisherBlacklistLevel.ADGROUP:
        blacklist_adgroup = ad_group

    return Q(
        everywhere=blacklist_global,
        account=blacklist_account,
        campaign=blacklist_campaign,
        ad_group=blacklist_adgroup
    )
