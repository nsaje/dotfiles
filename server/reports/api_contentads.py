import logging
import datetime
import pytz

from django.conf import settings

from reports import aggregate_fields
from reports import api_helpers
from reports import redshift
from reports import exc

from api_helpers import CONTENTADSTATS_FIELD_MAPPING
from api_helpers import CONTENTADSTATS_FIELD_REVERSE_MAPPING


logger = logging.getLogger(__name__)


def query(start_date, end_date, breakdown=None, **constraints):
    if breakdown and len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    results = redshift.query_contentadstats(
        start_date,
        end_date,
        aggregate_fields.ALL_AGGREGATE_FIELDS,
        CONTENTADSTATS_FIELD_MAPPING,
        breakdown,
        constraints)

    if breakdown:
        return [_transform_row(row) for row in results]

    return _transform_row(results)


def _transform_row(row):
    result = {}
    for name, val in row.items():
        name = CONTENTADSTATS_FIELD_REVERSE_MAPPING.get(name, name)

        val = aggregate_fields.transform_val(name, val)
        name = aggregate_fields.transform_name(name)

        result[name] = val

    return result


# TODO: Reimplement this for Redshift
def has_complete_postclick_metrics_accounts(start_date, end_date, accounts, sources):
    # TODO: Implement
    return True


def has_complete_postclick_metrics_campaigns(start_date, end_date, campaigns, sources):
    # TODO: Implement
    return True


def has_complete_postclick_metrics_ad_groups(start_date, end_date, ad_groups, sources):
    # TODO: Implement
    return True


def row_has_traffic_data(row):
    # TODO: Implement
    return True


def row_has_postclick_data(row):
    # TODO: Implement
    return True


def get_yesterday_cost(**constraints):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today = datetime.datetime(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)

    rs = get_day_cost(yesterday, breakdown=['source'], **constraints)

    result = {row['source']: row['cost'] for row in rs}
    return result


def get_day_cost(day, breakdown=None, **constraints):
    rs = query(
        start_date=day,
        end_date=day,
        breakdown=breakdown,
        **constraints
    )
    return rs
