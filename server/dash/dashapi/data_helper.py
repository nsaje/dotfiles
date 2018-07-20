from dash import constants
from dash import models


def campaign_has_available_budget(campaign):
    if campaign.real_time_campaign_stop:
        return True
    return campaign.budgets.all().filter_active().exists()


def filter_active_source_settings(ad_group_source_settings, ad_group_status_map):
    settings = []

    for source_settings in ad_group_source_settings:
        ad_group_id = source_settings["ad_group_id"]
        ad_group_status = ad_group_status_map[ad_group_id]

        status = get_source_status(source_settings["state"], ad_group_status)

        if status == constants.AdGroupSourceSettingsState.ACTIVE:
            settings.append(source_settings)

    return settings


def get_source_status(ad_group_source, source_state, ad_group_status):
    status = constants.AdGroupSourceSettingsState.INACTIVE
    if not ad_group_source.blockers and ad_group_status == constants.AdGroupSettingsState.ACTIVE:
        status = source_state
    return status


def get_ad_group_source_notification(ad_group_source, ad_group_settings, ad_group_source_settings):
    notification = {}
    if not models.AdGroup.is_ad_group_active(ad_group_settings):
        if ad_group_source_settings and ad_group_source_settings.state == constants.AdGroupSourceSettingsState.ACTIVE:
            notification["message"] = "This media source is enabled but will not run until" " you enable ad group."
            notification["important"] = True

    if ad_group_source.blockers:
        if ad_group_source_settings and ad_group_source_settings.state == constants.AdGroupSourceSettingsState.ACTIVE:
            reasons = [v for k, v in list(ad_group_source.blockers.items())]
            notification["message"] = "This media source is enabled but it is not running because: " + ", ".join(
                reasons
            )
            notification["important"] = True
    return notification
