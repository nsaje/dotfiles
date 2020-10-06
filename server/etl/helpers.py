import datetime

from dateutil import rrule

import backtosql
import dash.features.performance_tracking.constants
from utils import dates_helper


def get_local_date_query(date):
    context = get_local_date_context(date)
    # query only date first so redshift can use sort key
    query = """
        date >= '{tzdate_from}' and date <= '{tzdate_to}' and (
            (date = '{date}' and hour is null) or
            (hour is not null and (
                (date = '{tzdate_from}' and hour >= {tzhour_from}) or
                (date = '{tzdate_to}' and hour < {tzhour_to})
            ))
        )
    """.format(
        **context
    )
    return query


def get_local_date_context(date):
    """
    Prepare a date time context for aggregation of data by local time zone from UTC hourly data in the stats table.
    """

    hour_from = dates_helper.local_to_utc_time(datetime.datetime(date.year, date.month, date.day))
    date_next = date + datetime.timedelta(days=1)
    hour_to = dates_helper.local_to_utc_time(datetime.datetime(date_next.year, date_next.month, date_next.day))

    return {
        "date": date.isoformat(),
        "tzdate_from": hour_from.date().isoformat(),
        "tzhour_from": hour_from.hour,
        "tzdate_to": hour_to.date().isoformat(),
        "tzhour_to": hour_to.hour,
    }


def get_local_multiday_date_query(date_from, date_to):
    context = get_local_multiday_date_context(date_from, date_to)
    query = """
        date >= '{tzdate_from}' and date <= '{tzdate_to}' and (
            (date >= '{date_from} and date <= '{date_to}' and hour is null) or
            (hour is not null and (
                (date >= '{tzdate_from}' and hour >= {tzhour_from}) or
                (date <= '{tzdate_to}' and hour < {tzhour_to})
            ))
        )
    """.format(
        **context
    )
    return query


def get_local_multiday_date_context(date_from, date_to):
    """
    Prepare a date time context for multiday aggregation of data by local time zone
    from UTC hourly data in the stats table.
    """

    from_context = get_local_date_context(date_from)
    to_context = get_local_date_context(date_to)

    date_ranges = []
    for date in rrule.rrule(rrule.DAILY, dtstart=date_from, until=date_to):
        date_ranges.append(get_local_date_context(date.date()))

    return {
        "date_from": from_context["date"],
        "date_to": to_context["date"],
        "tzdate_from": from_context["tzdate_from"],
        "tzhour_from": from_context["tzhour_from"],
        "tzdate_to": to_context["tzdate_to"],
        "tzhour_to": to_context["tzhour_to"],
        "date_ranges": date_ranges,
    }


def calculate_effective_cost(cost, data_cost, factors):
    pct_actual_spend, pct_license_fee, pct_margin = factors

    effective_cost = cost * pct_actual_spend
    effective_data_cost = data_cost * pct_actual_spend
    license_fee = (effective_cost + effective_data_cost) * pct_license_fee
    margin = (effective_cost + effective_data_cost + license_fee) * pct_margin

    return effective_cost, effective_data_cost, license_fee, margin


def calculate_returning_users(users, new_visits):
    if users is None or new_visits is None:
        return None

    return max(0, users - new_visits)


def extract_source_slug(source_slug):
    if not source_slug:
        return None

    if source_slug.startswith("b1_"):
        return source_slug[3:]
    return source_slug


def get_highest_priority_postclick_source(rows_by_postclick_source):
    return rows_by_postclick_source.get(
        "gaapi",
        rows_by_postclick_source.get(
            "ga_mail", rows_by_postclick_source.get("omniture", rows_by_postclick_source.get("other", []))
        ),
    )


def extract_postclick_source(postclick_source):
    if postclick_source in ("gaapi", "ga_mail", "omniture"):
        return postclick_source
    return "other"


def get_breakdown_key_for_postclickstats(source_id, content_ad_id):
    # this is a helper function just so that we don't mess up the order of these

    return (source_id, content_ad_id)


def get_conversion_prefix(postclick_source, k):
    if postclick_source in ("gaapi", "ga_mail"):
        return dash.features.performance_tracking.constants.ReportType.GOOGLE_ANALYTICS + "__" + k
    if postclick_source in ("omniture",):
        return dash.features.performance_tracking.constants.ReportType.OMNITURE + "__" + k
    return k


def get_ad_group_ids_or_none(account_id):
    """ Some tables only have ad group ids, returns ad group ids if account_id is passed """

    if not account_id:
        return None

    return list(dash.models.AdGroup.objects.filter(campaign__account_id=account_id).values_list("pk", flat=True))


def prepare_create_timescale_hypertable(table_name: str):
    return backtosql.generate_sql("etl_create_timescale_hypertable.sql", dict(table_name=table_name))


def prepare_drop_timescale_hypertable_chunks(table_name: str, keep_days: int):
    return backtosql.generate_sql(
        "etl_drop_timescale_hypertable_chunks.sql", dict(table_name=table_name, keep_days=keep_days)
    )
