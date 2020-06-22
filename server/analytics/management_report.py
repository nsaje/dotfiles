from collections import OrderedDict
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string

import backtosql
from redshiftapi import db
from utils import csv_utils


def get_query_results():
    sql = backtosql.generate_sql("sql/management_report.sql", {})  # TODO: SERVICE FEE: will be handled by prodops
    with db.get_stats_cursor(settings.STATS_DB_HOT_CLUSTER) as c:
        c.execute(sql)
        return db.dictfetchall(c)


def prepare_report_as_csv(data):
    if data:
        return csv_utils.dictlist_to_csv(data[0].keys(), data)


def get_daily_report_html(data):
    context = {}
    if data:
        totals = dict.fromkeys(data[0].keys(), 0)
        for row in data:
            for k, v in row.items():
                if type(v) == Decimal:
                    totals[k] = sum([totals[k], v])
                    row[k] = "${:,.0f}".format(v)
                else:
                    totals[k] = ""

        context["data"] = [OrderedDict(d) for d in data]

        for k, v in totals.items():
            if type(v) == Decimal:
                totals[k] = "${:,.0f}".format(v)

        context["totals"] = totals

    return render_to_string("management_report.html", context)
