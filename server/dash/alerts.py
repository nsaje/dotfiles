def get_account_alerts(request, account):
    alerts = _get_account_default_icon_alert([], request, account)
    return alerts


def get_campaign_alerts(request, campaign):
    alerts = _get_account_default_icon_alert([], request, campaign.account)
    return alerts


def _get_account_default_icon_alert(alerts, request, account):
    if request.user and not request.user.has_perm("zemauth.can_use_creative_icon"):
        return alerts

    if account.settings.default_icon:
        return alerts

    alerts.append(
        {
            "type": "danger",
            "message": "Please add a brand logo to this account. "
            + "The logo will be added to your ads if required by media source. "
            + "Logo can be added on account-level settings. "
            + "Read more about brand logo "
            + "<a href='https://help.zemanta.com/article/show/100808-adding-brand-logo-to-content-ads'>here</a>.",
        }
    )
    return alerts
