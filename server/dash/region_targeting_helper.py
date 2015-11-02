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


def _get_region_types(*settings):
    region_types = []

    # build a list of region types present in the given settings
    for region_type in constants.RegionType.get_all():
        for iteration in settings:
            if iteration.targets_region_type(region_type):
                region_types.append(region_type)
                break

    return region_types