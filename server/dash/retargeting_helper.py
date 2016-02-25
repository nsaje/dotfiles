from dash import models


def can_be_retargeted(source, ad_group_settings):
    if source.can_modify_retargeting_automatically():
        return True

    # get all adgroup settings from this account
    account = ad_group_settings.ad_group.campaign.account
    other_adgss = models.AdGroupSettings.objects.filter(
        ad_group__campaign__account=account
    ).group_current_settings().exclude(
        ad_group=ad_group_settings.ad_group
    ).only('retargeting_ad_groups')

    # check if anyone is retargeting this ad_group
    if any([ad_group_settings.ad_group.id in other_adgs
            for other_adgs in other_adgss]):
        # if not we can still add this source
        return False

    # if this adgroup is retargeting other adgroups this
    # source also needs to support retargeting
    if ad_group_settings.retargeting_ad_groups != []:
        return False

    return True


def can_add_source_with_retargeting(source, ad_group_settings):
    '''
    A new media source can be added if settings don't have retargeting
    enabled or if source supports retargeting.
    '''
    if ad_group_settings.retargeting_ad_groups == []:
        return True

    return source.can_modify_retargeting_automatically()


def filter_retargetable(ad_groups):
    adgss = models.AdGroupSource.objects.filter(
        ad_group__in=ad_groups
    ).select_related('ad_group', 'source')

    for adgs in adgss:
        if not adgs.source.can_modify_retargeting_automatically():
            ad_groups = [adg for adg in ad_groups if adg.id != adgs.ad_group.id]

    return ad_groups
