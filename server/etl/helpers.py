import datetime

from dash import constants

from utils import dates_helper


def get_local_date_query(date):
    context = get_local_date_context(date)

    query = """
    (date = '{date}' and hour is null) or (
        hour is not null and (
            (date = '{tzdate_from}' and hour >= {tzhour_from}) or
            (date = '{tzdate_to}' and hour < {tzhour_to})
        )
    )
    """.format(**context)
    return query


def get_local_date_context(date):
    """
    Prepare a date time context for aggregation of data by local time zone from UTC hourly data in the stats table.
    """

    hour_from = dates_helper.local_to_utc_time(datetime.datetime(date.year, date.month, date.day))
    date_next = date + datetime.timedelta(days=1)
    hour_to = dates_helper.local_to_utc_time(datetime.datetime(date_next.year, date_next.month, date_next.day))

    return {
        'date': date.isoformat(),
        'tzdate_from': hour_from.date(),
        'tzhour_from': hour_from.hour,
        'tzdate_to': hour_to.date(),
        'tzhour_to': hour_to.hour,
    }


def calculate_effective_cost(cost, data_cost, factors):
    pct_actual_spend, pct_license_fee = factors

    effective_cost = cost * pct_actual_spend
    effective_data_cost = data_cost * pct_actual_spend
    license_fee = (effective_cost + effective_data_cost) * pct_license_fee

    return effective_cost, effective_data_cost, license_fee
