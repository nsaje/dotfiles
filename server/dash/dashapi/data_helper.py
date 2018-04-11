from dash import constants
from dash import models


def campaign_has_available_budget(campaign):
    return campaign.budgets.all().filter_active().exists()


def filter_active_source_settings(ad_group_source_settings, ad_group_status_map):
    settings = []

    for source_settings in ad_group_source_settings:
        ad_group_id = source_settings['ad_group_id']
        ad_group_status = ad_group_status_map[ad_group_id]

        status = get_source_status(source_settings['state'], ad_group_status)

        if status == constants.AdGroupSourceSettingsState.ACTIVE:
            settings.append(source_settings)

    return settings


# PRTODO (jurebajt): Is this deprecated?
def get_source_settings_stats(source_settings):
    cpcs = [x['cpc_cc'] for x in source_settings if x['cpc_cc'] is not None]
    caps = [x['daily_budget_cc'] for x in source_settings if x['daily_budget_cc'] is not None]
    statuses = [x['state'] for x in source_settings]

    active = constants.AdGroupSourceSettingsState.ACTIVE
    inactive = constants.AdGroupSourceSettingsState.INACTIVE

    return {
        'state': active if active in statuses else inactive,
        'status': active if active in statuses else inactive,
        'daily_budget': sum(caps) if caps else None,
        'min_bid_cpc': float(min(cpcs)) if cpcs else None,
        'max_bid_cpc': float(max(cpcs)) if cpcs else None,
    }


def get_source_status(ad_group_source, source_state, ad_group_status):
    status = constants.AdGroupSourceSettingsState.INACTIVE
    if not ad_group_source.blockers and ad_group_status == constants.AdGroupSettingsState.ACTIVE:
        status = source_state
    return status


def get_ad_group_source_notification(ad_group_source, ad_group_settings, ad_group_source_settings):
    notification = {}
    if not models.AdGroup.is_ad_group_active(ad_group_settings):
        if ad_group_source_settings and ad_group_source_settings.state == constants.AdGroupSourceSettingsState.ACTIVE:
            notification['message'] = ('This media source is enabled but will not run until'
                                       ' you enable ad group.')
            notification['important'] = True

    if ad_group_source.blockers:
        if ad_group_source_settings and ad_group_source_settings.state == constants.AdGroupSourceSettingsState.ACTIVE:
            reasons = [v for k, v in list(ad_group_source.blockers.items())]
            notification['message'] = 'This media source is enabled but it is not running because: ' + ', '.join(reasons)
            notification['important'] = True
    return notification
