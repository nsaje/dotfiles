from dash import models


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
