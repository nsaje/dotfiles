import stats.constants as sc

DEVICE = {sc.DEVICE, sc.DEVICE_OS}
ENVIRONMENT = {sc.ENVIRONMENT, sc.ZEM_PLACEMENT_TYPE, sc.VIDEO_PLAYBACK_METHOD}
GEO = {sc.COUNTRY, sc.REGION, sc.DMA}
DEMO = {sc.AGE, sc.GENDER, sc.AGE_GENDER}
OTHER = {"device_os_version"}

ACCOUNT = {sc.ACCOUNT, sc.SOURCE}
CAMPAIGN_N_ABOVE = {sc.CAMPAIGN} | ACCOUNT
AD_GROUP_N_ABOVE = {sc.AD_GROUP} | CAMPAIGN_N_ABOVE
CONTENT_AD_N_ABOVE = {sc.CONTENT_AD} | AD_GROUP_N_ABOVE
PUBLISHER_N_ABOVE = {sc.PUBLISHER} | AD_GROUP_N_ABOVE

BASE_VIEWS = [
    ["mv_account", ACCOUNT],
    ["mv_account_device", ACCOUNT | DEVICE],
    ["mv_account_environment", ACCOUNT | ENVIRONMENT],
    ["mv_account_geo", ACCOUNT | GEO],
    ["mv_campaign", CAMPAIGN_N_ABOVE],
    ["mv_campaign_device", CAMPAIGN_N_ABOVE | DEVICE],
    ["mv_campaign_environment", CAMPAIGN_N_ABOVE | ENVIRONMENT],
    ["mv_campaign_geo", CAMPAIGN_N_ABOVE | GEO],
    ["mv_adgroup", AD_GROUP_N_ABOVE],
    ["mv_adgroup_device", AD_GROUP_N_ABOVE | DEVICE],
    ["mv_adgroup_environment", AD_GROUP_N_ABOVE | ENVIRONMENT],
    ["mv_adgroup_geo", AD_GROUP_N_ABOVE | GEO],
    ["mv_contentad", CONTENT_AD_N_ABOVE],
    ["mv_contentad_device", CONTENT_AD_N_ABOVE | DEVICE],
    ["mv_contentad_environment", CONTENT_AD_N_ABOVE | ENVIRONMENT],
    ["mv_contentad_geo", CONTENT_AD_N_ABOVE | GEO],
    ["mv_master", CONTENT_AD_N_ABOVE | {sc.PUBLISHER} | DEVICE | ENVIRONMENT | GEO | DEMO | OTHER],
]


PUBLISHER_VIEWS = [
    ["mv_account_pubs", ACCOUNT | {sc.PUBLISHER}],
    ["mv_campaign_pubs", CAMPAIGN_N_ABOVE | {sc.PUBLISHER}],
    ["mv_adgroup_pubs", AD_GROUP_N_ABOVE | {sc.PUBLISHER}],
    ["mv_master_pubs", AD_GROUP_N_ABOVE | {sc.PUBLISHER} | DEVICE | ENVIRONMENT | GEO | DEMO | OTHER],
]


CONVERSION_VIEWS = [
    ["mv_account_conv", ACCOUNT],
    ["mv_campaign_conv", CAMPAIGN_N_ABOVE],
    ["mv_adgroup_conv", AD_GROUP_N_ABOVE],
    ["mv_contentad_conv", CONTENT_AD_N_ABOVE],
    ["mv_conversions", CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]


TOUCH_DEVICE = {sc.DEVICE, sc.DEVICE_OS}
TOUCH_ENVIRONMENT = {sc.ENVIRONMENT}
TOUCH_GEO = {sc.COUNTRY, sc.REGION, sc.DMA}

TOUCHPOINT_VIEWS = [
    ["mv_account_touch", ACCOUNT],
    ["mv_account_touch_device", ACCOUNT | TOUCH_DEVICE],
    ["mv_account_touch_environment", ACCOUNT | TOUCH_ENVIRONMENT],
    ["mv_account_touch_geo", ACCOUNT | TOUCH_GEO],
    ["mv_campaign_touch", CAMPAIGN_N_ABOVE],
    ["mv_campaign_touch_device", CAMPAIGN_N_ABOVE | TOUCH_DEVICE],
    ["mv_campaign_touch_environment", CAMPAIGN_N_ABOVE | TOUCH_ENVIRONMENT],
    ["mv_campaign_touch_geo", CAMPAIGN_N_ABOVE | TOUCH_GEO],
    ["mv_adgroup_touch", AD_GROUP_N_ABOVE],
    ["mv_adgroup_touch_device", AD_GROUP_N_ABOVE | TOUCH_DEVICE],
    ["mv_adgroup_touch_environment", AD_GROUP_N_ABOVE | TOUCH_ENVIRONMENT],
    ["mv_adgroup_touch_geo", AD_GROUP_N_ABOVE | TOUCH_GEO],
    ["mv_contentad_touch", CONTENT_AD_N_ABOVE],
    ["mv_contentad_touch_device", CONTENT_AD_N_ABOVE | TOUCH_DEVICE],
    ["mv_contentad_touch_environment", CONTENT_AD_N_ABOVE | TOUCH_ENVIRONMENT],
    ["mv_contentad_touch_geo", CONTENT_AD_N_ABOVE | TOUCH_GEO],
    ["mv_touchpointconversions", CONTENT_AD_N_ABOVE | {sc.PUBLISHER} | DEVICE | {sc.ENVIRONMENT} | GEO],
]


def supports_external_id(view):
    return view in [x[0] for x in PUBLISHER_VIEWS]


def supports_conversions(base_view, conversions_view):
    return bool(base_view and conversions_view)


def get_fitting_view_dict(needed_dimensions, views):
    needed_dimensions = set(needed_dimensions) - set(sc.TimeDimension._ALL)

    for view, available in views:
        if len(needed_dimensions - available) == 0:
            return view

    return None


def get_best_view_base(needed_dimensions, use_publishers_view):
    return get_fitting_view_dict(needed_dimensions, PUBLISHER_VIEWS if use_publishers_view else BASE_VIEWS)


def get_best_view_conversions(needed_dimensions):
    return get_fitting_view_dict(needed_dimensions, CONVERSION_VIEWS)


def get_best_view_touchpoints(needed_dimensions):
    return get_fitting_view_dict(needed_dimensions, TOUCHPOINT_VIEWS)
