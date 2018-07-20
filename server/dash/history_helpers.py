import dash.constants
import dash.models


def write_global_history(changes_text, user=None, system_user=None, action_type=None):
    if not changes_text:
        # don't write history in case of no changes
        return None

    return dash.models.History.objects.create(
        created_by=user,
        system_user=system_user,
        changes_text=changes_text or "",
        level=dash.constants.HistoryLevel.GLOBAL,
        action_type=action_type,
    )


def get_ad_group_history(ad_group):
    return (
        dash.models.History.objects.all()
        .filter(ad_group=ad_group, level=dash.constants.HistoryLevel.AD_GROUP)
        .order_by("-created_dt")
    )


def get_campaign_history(campaign):
    return (
        dash.models.History.objects.all()
        .filter(campaign=campaign, level=dash.constants.HistoryLevel.CAMPAIGN)
        .order_by("-created_dt")
    )


def get_account_history(account):
    return (
        dash.models.History.objects.all()
        .filter(account=account, level=dash.constants.HistoryLevel.ACCOUNT)
        .order_by("-created_dt")
    )


def get_agency_history(agency):
    return (
        dash.models.History.objects.all()
        .filter(agency=agency, level=dash.constants.HistoryLevel.AGENCY)
        .order_by("-created_dt")
    )
