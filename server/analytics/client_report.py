import datetime

from django.template.loader import render_to_string
from django.db import models

import zemauth.models
import dash.models
import dash.constants

from utils.html_helpers import TableCell, TableRow, Url


def _group_blacklisting_actions(date, active_account_ids):
    actions = {}
    entries = dash.models.History.objects.filter(
        action_type__in=(dash.constants.HistoryActionType.PUBLISHER_BLACKLIST_CHANGE,),
        account_id__in=active_account_ids,
        created_dt__lt=date,
        created_dt__gte=date - datetime.timedelta(8),
    )
    for entry in entries:
        if not entry.account_id:
            continue
        if entry.account_id not in actions:
            actions[entry.account_id] = 0
        actions[entry.account_id] += 1
    return actions


def _group_selfmanaged_actions(date, active_account_ids):
    actions = {}
    history = dash.models.History.objects.filter(
        account_id__in=active_account_ids, created_dt__lt=date, created_dt__gte=date - datetime.timedelta(8)
    ).filter_selfmanaged()
    for action in history:
        if action.account_id not in actions:
            actions[action.account_id] = 0
        actions[action.account_id] += 1
    return actions


def _group_seen_users(date, active_account_ids):
    actions = (
        dash.models.History.objects.filter(
            account_id__in=active_account_ids, created_dt__gte=date - datetime.timedelta(8), created_dt__lt=date
        )
        .filter_selfmanaged()
        .distinct("created_by_id")
    )
    user_ids = zemauth.models.User.objects.all().filter(pk__in=actions.values_list("created_by_id", flat=True))
    seen = {}
    for user in user_ids:
        accounts = dash.models.Account.objects.filter(models.Q(users__in=[user]) | models.Q(agency__users__in=[user]))
        for acc in accounts:
            seen.setdefault(acc, set()).add(user)
    return {acc.pk: len(acc_users) for acc, acc_users in seen.items()}


def _prepare_table_rows(date):
    active_account_ids = (
        dash.models.AdGroup.objects.all()
        .filter_active()
        .select_related("campaign")
        .values_list("campaign__account_id", flat=True)
    )

    seen = _group_seen_users(date, active_account_ids)
    actions = _group_selfmanaged_actions(date, active_account_ids)
    blacklist = _group_blacklisting_actions(date, active_account_ids)

    rows, totals = [], []
    for account in dash.models.Account.objects.filter(pk__in=active_account_ids):
        rows.append(
            TableRow(
                [
                    TableCell(
                        Url(
                            "https://one.zemanta.com/v2/analytics/campaign/{}".format(account.pk),
                            account.get_long_name(),
                        ).as_html()
                    ),
                    TableCell(blacklist.get(account.pk, 0)),
                    TableCell(actions.get(account.pk, 0)),
                    TableCell(seen.get(account.pk, 0)),
                ]
            )
        )

    header = [
        TableRow(
            list(
                map(
                    TableCell,
                    [
                        date.strftime("%B %d"),
                        "# blacklisted publishers",
                        "# self-managed actions",
                        "# different users seen",
                    ],
                )
            )
        )
    ]
    totals = [
        TableRow(
            list(map(TableCell, ["", sum(blacklist.values()), sum(actions.values()), sum(seen.values())])),
            row_type=TableRow.TYPE_TOTALS,
        )
    ]
    return header + _sort_rows(rows) + totals


def _sort_rows(rows):
    return list(sorted(rows, key=lambda r: r[2].value, reverse=True))


def _generate_table_html(date):
    html = '<table style="width:100%" cellspacing="5px" cellpading="2px"><caption>Daily Management Report</caption>'
    for position, row in enumerate(_prepare_table_rows(date)):
        html += row.as_html(position)
    html += "</table>"
    return html


def get_weekly_report_html(date=None):
    if not date:
        date = datetime.date.today()
    return render_to_string("client_report.html", {"table": _generate_table_html(date)})
