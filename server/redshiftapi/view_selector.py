import stats.constants as sc

PUBLISHER = {sc.PUBLISHER}
PLACEMENT = {sc.PLACEMENT}
ENVIRONMENT = {sc.ENVIRONMENT, sc.ZEM_PLACEMENT_TYPE, sc.VIDEO_PLAYBACK_METHOD}
DEVICE = {sc.DEVICE, sc.DEVICE_OS, sc.BROWSER, sc.CONNECTION_TYPE}
GEO = {sc.COUNTRY, sc.REGION, sc.DMA}
DEMO = {sc.AGE, sc.GENDER, sc.AGE_GENDER}
OTHER = {"device_os_version"}

ACCOUNT = {sc.ACCOUNT, sc.SOURCE}
CAMPAIGN_N_ABOVE = {sc.CAMPAIGN} | ACCOUNT
AD_GROUP_N_ABOVE = {sc.AD_GROUP} | CAMPAIGN_N_ABOVE
CONTENT_AD_N_ABOVE = {sc.CONTENT_AD} | AD_GROUP_N_ABOVE

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
    ["mv_master", CONTENT_AD_N_ABOVE | PUBLISHER | ENVIRONMENT | DEVICE | GEO | DEMO | OTHER],
]


PUBLISHER_VIEWS = [
    ["mv_account_pubs", ACCOUNT | PUBLISHER],
    ["mv_campaign_pubs", CAMPAIGN_N_ABOVE | PUBLISHER],
    ["mv_adgroup_pubs", AD_GROUP_N_ABOVE | PUBLISHER],
    ["mv_master", AD_GROUP_N_ABOVE | PUBLISHER | ENVIRONMENT | DEVICE | GEO | DEMO | OTHER],
    ["mv_account_placement", ACCOUNT | PUBLISHER | PLACEMENT],
    ["mv_campaign_placement", CAMPAIGN_N_ABOVE | PUBLISHER | PLACEMENT],
    ["mv_adgroup_placement", AD_GROUP_N_ABOVE | PUBLISHER | PLACEMENT],
]


CONVERSION_VIEWS = [
    ["mv_account_conv", ACCOUNT],
    ["mv_campaign_conv", CAMPAIGN_N_ABOVE],
    ["mv_adgroup_conv", AD_GROUP_N_ABOVE],
    ["mv_contentad_conv", CONTENT_AD_N_ABOVE],
    ["mv_conversions", CONTENT_AD_N_ABOVE | PUBLISHER],
]

TOUCH_BASE = {"slug", "window"}
TOUCH_ENVIRONMENT = {sc.ENVIRONMENT}

TOUCHPOINT_VIEWS = [
    ["mv_account_touch", TOUCH_BASE | ACCOUNT],
    ["mv_account_touch_device", TOUCH_BASE | ACCOUNT | DEVICE],
    ["mv_account_touch_environment", TOUCH_BASE | ACCOUNT | TOUCH_ENVIRONMENT],
    ["mv_account_touch_geo", TOUCH_BASE | ACCOUNT | GEO],
    [
        "mv_account_touch_placement",
        TOUCH_BASE | ACCOUNT | PLACEMENT,
    ],  # TODO: plac: add PUBLISHER back after table correctly replicated
    ["mv_campaign_touch", TOUCH_BASE | CAMPAIGN_N_ABOVE],
    ["mv_campaign_touch_device", TOUCH_BASE | CAMPAIGN_N_ABOVE | DEVICE],
    ["mv_campaign_touch_environment", TOUCH_BASE | CAMPAIGN_N_ABOVE | TOUCH_ENVIRONMENT],
    ["mv_campaign_touch_geo", TOUCH_BASE | CAMPAIGN_N_ABOVE | GEO],
    [
        "mv_campaign_touch_placement",
        TOUCH_BASE | CAMPAIGN_N_ABOVE | PLACEMENT,
    ],  # TODO: plac: add PUBLISHER back after table correctly replicated
    ["mv_adgroup_touch", TOUCH_BASE | AD_GROUP_N_ABOVE],
    ["mv_adgroup_touch_device", TOUCH_BASE | AD_GROUP_N_ABOVE | DEVICE],
    ["mv_adgroup_touch_environment", TOUCH_BASE | AD_GROUP_N_ABOVE | TOUCH_ENVIRONMENT],
    ["mv_adgroup_touch_geo", TOUCH_BASE | AD_GROUP_N_ABOVE | GEO],
    [
        "mv_adgroup_touch_placement",
        TOUCH_BASE | AD_GROUP_N_ABOVE | PLACEMENT,
    ],  # TODO: plac: add PUBLISHER back after table correctly replicated
    ["mv_contentad_touch", TOUCH_BASE | CONTENT_AD_N_ABOVE],
    ["mv_contentad_touch_device", TOUCH_BASE | CONTENT_AD_N_ABOVE | DEVICE],
    ["mv_contentad_touch_environment", TOUCH_BASE | CONTENT_AD_N_ABOVE | TOUCH_ENVIRONMENT],
    ["mv_contentad_touch_geo", TOUCH_BASE | CONTENT_AD_N_ABOVE | GEO],
    [
        "mv_touchpointconversions",
        TOUCH_BASE | CONTENT_AD_N_ABOVE | PUBLISHER | PLACEMENT | TOUCH_ENVIRONMENT | DEVICE | GEO,
    ],
]


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
