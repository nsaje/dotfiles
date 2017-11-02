import stats.constants as sc


DEVICE = {sc.DEVICE, sc.DEVICE_OS}
PLACEMENT = {sc.PLACEMENT_MEDIUM, sc.PLACEMENT_TYPE, sc.VIDEO_PLAYBACK_METHOD}
GEO = {sc.COUNTRY, sc.STATE, sc.DMA}
DEMO = {sc.AGE, sc.GENDER, sc.AGE_GENDER}
OTHER = {'device_os_version'}

ACCOUNT = {sc.ACCOUNT, sc.SOURCE}
CAMPAIGN_N_ABOVE = {sc.CAMPAIGN} | ACCOUNT
AD_GROUP_N_ABOVE = {sc.AD_GROUP} | CAMPAIGN_N_ABOVE
CONTENT_AD_N_ABOVE = {sc.CONTENT_AD} | AD_GROUP_N_ABOVE
PUBLISHER_N_ABOVE = {sc.PUBLISHER} | AD_GROUP_N_ABOVE

BASE_VIEWS = [
    ['mv_account', ACCOUNT],
    ['mv_account_device', ACCOUNT | DEVICE],
    ['mv_account_placement', ACCOUNT | PLACEMENT],
    ['mv_account_geo', ACCOUNT | GEO],

    ['mv_campaign', CAMPAIGN_N_ABOVE],
    ['mv_campaign_device', CAMPAIGN_N_ABOVE | DEVICE],
    ['mv_campaign_placement', CAMPAIGN_N_ABOVE | PLACEMENT],
    ['mv_campaign_geo', CAMPAIGN_N_ABOVE | GEO],

    ['mv_adgroup', AD_GROUP_N_ABOVE],
    ['mv_adgroup_device', AD_GROUP_N_ABOVE | DEVICE],
    ['mv_adgroup_placement', AD_GROUP_N_ABOVE | PLACEMENT],
    ['mv_adgroup_geo', AD_GROUP_N_ABOVE | GEO],

    ['mv_contentad', CONTENT_AD_N_ABOVE],
    ['mv_contentad_device', CONTENT_AD_N_ABOVE | DEVICE],
    ['mv_contentad_placement', CONTENT_AD_N_ABOVE | PLACEMENT],
    ['mv_contentad_geo', CONTENT_AD_N_ABOVE | GEO],

    ['mv_master', CONTENT_AD_N_ABOVE | {sc.PUBLISHER} | DEVICE | PLACEMENT | GEO | DEMO | OTHER],
]


PUBLISHER_VIEWS = [
    ['mv_account_pubs', ACCOUNT | {sc.PUBLISHER}],
    ['mv_campaign_pubs', CAMPAIGN_N_ABOVE | {sc.PUBLISHER}],
    ['mv_adgroup_pubs', AD_GROUP_N_ABOVE | {sc.PUBLISHER}],
    ['mv_master_pubs', AD_GROUP_N_ABOVE | {sc.PUBLISHER} | DEVICE | PLACEMENT | GEO | DEMO | OTHER],
]


CONVERSION_VIEWS = [
    ['mv_account_conv', ACCOUNT],
    ['mv_campaign_conv', CAMPAIGN_N_ABOVE],
    ['mv_adgroup_conv', AD_GROUP_N_ABOVE],
    ['mv_contentad_conv', CONTENT_AD_N_ABOVE],
    ['mv_conversions', CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]


TOUCHPOINT_VIEWS = [
    ['mv_account_touch', ACCOUNT],
    ['mv_campaign_touch', CAMPAIGN_N_ABOVE],
    ['mv_adgroup_touch', AD_GROUP_N_ABOVE],
    ['mv_contentad_touch', CONTENT_AD_N_ABOVE],
    ['mv_touchpointconversions', CONTENT_AD_N_ABOVE | {sc.PUBLISHER}],
]


def supports_publisher_id(view):
    views = set(x[0] for x in PUBLISHER_VIEWS) | {'mv_master', 'mv_conversions', 'mv_touchpointconversions'}
    return view in views


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
    return get_fitting_view_dict(
        needed_dimensions, PUBLISHER_VIEWS if use_publishers_view else BASE_VIEWS)


def get_best_view_conversions(needed_dimensions):
    return get_fitting_view_dict(needed_dimensions, CONVERSION_VIEWS)


def get_best_view_touchpoints(needed_dimensions):
    return get_fitting_view_dict(needed_dimensions, TOUCHPOINT_VIEWS)
