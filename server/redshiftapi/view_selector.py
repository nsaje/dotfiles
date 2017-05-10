import stats.constants as sc


GEO = set([sc.COUNTRY, sc.STATE, sc.DMA])
DEMO = set([sc.DEVICE, sc.AGE, sc.GENDER, sc.AGE_GENDER])
VIDEO = set([sc.PLACEMENT_TYPE, sc.VIDEO_PLAYBACK_METHOD])

ACCOUNT = {sc.ACCOUNT, sc.SOURCE}
CAMPAIGN_N_ABOVE = {sc.CAMPAIGN} | ACCOUNT
AD_GROUP_N_ABOVE = {sc.AD_GROUP} | CAMPAIGN_N_ABOVE
CONTENT_AD_N_ABOVE = {sc.CONTENT_AD} | AD_GROUP_N_ABOVE

BASE_VIEWS = [
    ['mv_account', ACCOUNT],
    ['mv_account_delivery_geo', ACCOUNT | GEO],
    ['mv_account_delivery_demo', ACCOUNT | DEMO],

    ['mv_campaign', CAMPAIGN_N_ABOVE],
    ['mv_campaign_delivery_geo', CAMPAIGN_N_ABOVE | GEO],
    ['mv_campaign_delivery_demo', CAMPAIGN_N_ABOVE | DEMO],

    ['mv_ad_group', AD_GROUP_N_ABOVE],
    ['mv_ad_group_delivery_geo', AD_GROUP_N_ABOVE | GEO],
    ['mv_ad_group_delivery_demo', AD_GROUP_N_ABOVE | DEMO],

    ['mv_content_ad', CONTENT_AD_N_ABOVE],
    ['mv_content_ad_delivery_geo', CONTENT_AD_N_ABOVE | GEO],
    ['mv_content_ad_delivery_demo', CONTENT_AD_N_ABOVE | DEMO],

    ['mv_master', CONTENT_AD_N_ABOVE | {sc.PUBLISHER} | GEO | DEMO | VIDEO],
]


PUBLISHER_VIEWS = [
    ['mv_pubs_ad_group', AD_GROUP_N_ABOVE | {sc.PUBLISHER}],
    ['mv_pubs_master', AD_GROUP_N_ABOVE | {sc.PUBLISHER} | GEO | DEMO],
]


CONVERSION_VIEWS = [
    ['mv_conversions_account', ACCOUNT],
    ['mv_conversions_campaign', CAMPAIGN_N_ABOVE],
    ['mv_conversions_ad_group', AD_GROUP_N_ABOVE],
    ['mv_conversions_content_ad', CONTENT_AD_N_ABOVE],
    ['mv_conversions', CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]

CONVERSIONS_PUBLISHERS_VIEWS = [
    ['mv_conversions', CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]


TOUCHPOINT_VIEWS = [
    ['mv_touch_account', ACCOUNT],
    ['mv_touch_campaign', CAMPAIGN_N_ABOVE],
    ['mv_touch_ad_group', AD_GROUP_N_ABOVE],
    ['mv_touch_content_ad', CONTENT_AD_N_ABOVE],
    ['mv_touchpointconversions', CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]

TOUCHPOINTS_PUBLISHERS_VIEWS = [
    ['mv_touchpointconversions', CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]


def get_fitting_view_dict(needed_dimensions, views):
    needed_dimensions = set(needed_dimensions) - set(sc.TimeDimension._ALL)

    for view, available in views:
        if len(needed_dimensions - available) == 0:
            return view
    return None


def get_best_view_base(needed_dimensions, use_publishers_view):
    return get_fitting_view_dict(
        needed_dimensions, PUBLISHER_VIEWS if use_publishers_view else BASE_VIEWS)


def get_best_view_conversions(needed_dimensions, use_publishers_view):
    return get_fitting_view_dict(
        needed_dimensions, CONVERSIONS_PUBLISHERS_VIEWS if use_publishers_view else CONVERSION_VIEWS)


def get_best_view_touchpoints(needed_dimensions, use_publishers_view):
    return get_fitting_view_dict(
        needed_dimensions, TOUCHPOINTS_PUBLISHERS_VIEWS if use_publishers_view else TOUCHPOINT_VIEWS)


def supports_conversions(needed_dimensions, use_publishers_view):
    return bool(
        get_best_view_conversions(needed_dimensions, use_publishers_view) and get_best_view_touchpoints(
            needed_dimensions, use_publishers_view))
