import datetime

import dash.constants
import stats.constants

ACCOUNT_DEFAULT_ICON_ALERT = (
    "Please add a brand logo to this account. "
    "The logo will be added to your ads if required by media source. "
    "Logo can be added on account-level settings. "
    "Read more about brand logo "
    "<a href='https://help.zemanta.com/article/show/100808-adding-brand-logo-to-content-ads'>here</a>."
)

PLACEMENT_CONVERSIONS_START_DATE = "2020-04-15"
PLACEMENT_CONVERSIONS_ALERT = (
    "You have selected date range including dates before 15th of April "
    "which may result in displaying certain conversion data only as total "
    "and not as individual placement breakdown."
)


def get_accounts_alerts(request, **kwargs):
    alerts = _get_placement_conversion_alert([], request, **kwargs)
    return alerts


def get_account_alerts(request, account, **kwargs):
    alerts = _get_account_default_icon_alert([], request, account)
    alerts = _get_placement_conversion_alert(alerts, request, **kwargs)
    return alerts


def get_campaign_alerts(request, campaign, **kwargs):
    alerts = _get_account_default_icon_alert([], request, campaign.account)
    alerts = _get_placement_conversion_alert(alerts, request, **kwargs)
    return alerts


def get_ad_group_alerts(request, ad_group, **kwargs):
    alerts = _get_account_default_icon_alert([], request, ad_group.campaign.account)
    alerts = _get_placement_conversion_alert(alerts, request, **kwargs)
    return alerts


def _get_account_default_icon_alert(alerts, request, account):
    if account.settings.default_icon:
        return alerts

    alerts.append({"type": dash.constants.AlertType.DANGER, "message": ACCOUNT_DEFAULT_ICON_ALERT, "is_closable": True})
    return alerts


def _get_placement_conversion_alert(alerts, request, **kwargs):
    if request.user and not request.user.has_perm("zemauth.can_use_placement_targeting"):
        return alerts

    breakdown = kwargs.get("breakdown")
    if not breakdown:
        return alerts

    if breakdown != stats.constants.DimensionIdentifier.PLACEMENT:
        return alerts

    start_date = kwargs.get("start_date")
    if not start_date:
        return alerts

    placement_conversions_start_date = datetime.datetime.strptime(PLACEMENT_CONVERSIONS_START_DATE, "%Y-%m-%d").date()
    if placement_conversions_start_date <= start_date:
        return alerts

    alerts.append(
        {"type": dash.constants.AlertType.WARNING, "message": PLACEMENT_CONVERSIONS_ALERT, "is_closable": True}
    )
    return alerts
