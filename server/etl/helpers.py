import datetime

from dash import constants

from utils import dates_helper


def get_local_date_context(date):
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
