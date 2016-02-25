from dash import constants
from dash import regions


def get_list_for_region_type(region_type):
    if region_type == constants.RegionType.COUNTRY:
        return regions.COUNTRY_BY_CODE
    elif region_type == constants.RegionType.SUBDIVISION:
        return regions.SUBDIVISION_BY_CODE
    elif region_type == constants.RegionType.DMA:
        return regions.DMA_BY_CODE


def can_modify_selected_target_regions_automatically(source, *settings):
    region_types = _get_region_types(*settings)

    # check for each region_type found if the source supports automatic modification
    for region_type in region_types:
        if not source.can_modify_targeting_for_region_type_automatically(region_type):
            return False

    return True


def can_modify_selected_target_regions_manually(source, *settings):
    region_types = _get_region_types(*settings)

    # check for each region_type found if the source supports manual modification
    for region_type in region_types:
        if not source.can_modify_targeting_for_region_type_manually(region_type):
            return False

    return True


def can_target_existing_regions(source, *settings):
    return can_modify_selected_target_regions_automatically(source, *settings) or \
            can_modify_selected_target_regions_manually(source, *settings)


def _get_region_types(*settings):
    region_types = []

    # build a list of region types present in the given settings
    for region_type in constants.RegionType.get_all():
        for iteration in settings:
            if iteration.targets_region_type(region_type):
                region_types.append(region_type)
                break

    return region_types


def can_be_retargeted(source, ad_group_settings):
    if source.can_modify_retargeting_automatically():
        return True

    # get all adgroup settings from this account
    account = ad_group_settings.ad_group.campaign.account
    other_adgss = models.AdGroupSettings.objects.filter(
        ad_group__campaign_account=account
    ).group_current_settings().exclude(
        ad_group=ad_group_settings.ad_group
    ).only('retargeting_ad_groups')

    # check if anyone is retargeting this ad_group
    if any([ad_group_settings.ad_group.id in other_adgs
            for other_adgs in other_adgss]):
        # if not we can still add this source
        return False
    else:
        return True


def can_add_source_with_retargeting(source, ad_group_settings):
    '''
    A new media source can be added if settings don't have retargeting
    enabled or if source supports retargeting.
    '''
    if ad_group_settings.retargeting_ad_groups == []:
        return True

    return source.can_modify_retargeting_automatically()
