from collections import OrderedDict
from decimal import Decimal

from django.template.loader import render_to_string

import backtosql
from redshiftapi import db
from utils import csv_utils


def get_query_results():
    sql = backtosql.generate_sql("sql/management_report.sql", {})
    with db.get_stats_cursor() as c:
        c.execute(sql)
        return db.dictfetchall(c)


def prepare_report_as_csv(data):
    if data:
        return csv_utils.dictlist_to_csv(data[0].keys(), data)


def get_daily_report_html(data):
    context = {}
    if data:
        for row in data:
            for k, v in row.items():
                if type(v) == Decimal:
                    row[k] = "${}".format(round(v))

        context["data"] = [OrderedDict(d) for d in data]

    return render_to_string("management_report.html", context)
