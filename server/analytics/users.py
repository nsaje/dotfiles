import datetime

from dash import constants
import zemauth.models
import dash.models


def _get_api_user_emails():
    return set(
        u.email
        for u in zemauth.models.User.objects.filter(
            groups__id=33, is_test_user=True, last_login__gte=datetime.date.today() - datetime.timedelta(8)
        )
        if not u.email.endswith("@zemanta.com")
        and "andraz.tori" not in u.email
        and not u.email.endswith("@zemanta-test.com")
    )


HEADER = (
    "id",
    "agency",
    "account",
    "campaign",
    "ad_group",
    "level",
    "action_type",
    "changes_text",
    "created_dt",
    "system_user",
    "created_by",
)


def _self_managed(queryset):
    return (
        queryset.filter(created_by__email__isnull=False)
        .exclude(created_by__email__icontains="@zemanta")
        .exclude(created_by__is_test_user=True)
        .exclude(action_type__isnull=True)
    )


def _get_name(obj):
    return obj.name if obj else "/"


def _row(obj):
    return (
        obj.id,
        _get_name(obj.agency),
        _get_name(obj.account),
        _get_name(obj.campaign),
        _get_name(obj.ad_group),
        constants.HistoryLevel.get_text(obj.level),
        constants.HistoryActionType.get_text(obj.action_type),
        obj.changes_text,
        obj.created_dt,
        obj.system_user and constants.SystemUserType.get_text(obj.system_user) or "/",
        obj.created_by.email if obj.created_by else "/",
    )


def get_wau_api_report():
    users = zemauth.models.User.objects.filter(email__in=_get_api_user_emails())
    actions = dash.models.History.objects.filter(
        created_by__in=users,
        created_dt__gte=datetime.date.today() - datetime.timedelta(8),
        created_dt__lt=datetime.date.today(),
    ).select_related("agency", "account", "campaign", "ad_group")
    data = [_row(obj) for obj in actions]
    return [HEADER] + data
