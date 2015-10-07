import decimal

from django.db.models import Sum

from utils import db_aggregates

CLICKS_SUM = 'clicks_sum'
IMPRESSIONS_SUM = 'impressions_sum'
COST_CC_SUM = 'cost_cc_sum'
CTR = 'ctr'
CPC_CC = 'cpc_cc'

VISITS_SUM = 'visits_sum'
NEW_VISITS_SUM = 'new_visits_sum'
PERCENT_NEW_USERS = 'percent_new_users'
BOUNCE_RATE = 'bounce_rate'
PAGEVIEWS_SUM = 'pageviews_sum'
PV_PER_VISIT = 'pv_per_visit'
AVG_TOS = 'avg_tos'
CLICK_DISCREPANCY = 'click_discrepancy'

CONVERSIONS_SUM = 'conversions_sum'
CONVERSIONS_VALUE_CC_SUM = 'conversions_value_cc_sum'

AGGREGATE_FIELDS = dict(
    clicks_sum=Sum('clicks'),
    impressions_sum=Sum('impressions'),
    cost_cc_sum=Sum('cost_cc'),
    ctr=db_aggregates.SumDivision('clicks', 'impressions'),
    cpc_cc=db_aggregates.SumDivision('cost_cc', 'clicks')
)

POSTCLICK_AGGREGATE_FIELDS = dict(
    visits_sum=Sum('visits'),
    new_visits_sum=Sum('new_visits'),
    pageviews_sum=Sum('pageviews'),
    percent_new_users=db_aggregates.SumDivision('new_visits', 'visits'),
    bounce_rate=db_aggregates.SumDivision('bounced_visits', 'visits'),
    pv_per_visit=db_aggregates.SumDivision('pageviews', 'visits'),
    avg_tos=db_aggregates.SumDivision('duration', 'visits'),
    # click_discrepancy is hidden in redshift
)

GOAL_AGGREGATE_FIELDS = dict(
    conversions_sum=Sum('conversions'),
    conversions_value_cc_sum=Sum('conversions_value_cc'),
)


def transform_name(name):
    name_translate = {
        CLICKS_SUM: 'clicks',
        IMPRESSIONS_SUM: 'impressions',
        COST_CC_SUM: 'cost',
        CPC_CC: 'cpc',
        VISITS_SUM: 'visits',
        NEW_VISITS_SUM: 'new_visits',
        PAGEVIEWS_SUM: 'pageviews',
        CONVERSIONS_VALUE_CC_SUM: 'conversion_value',
        CONVERSIONS_SUM: 'conversions'
    }

    return name_translate.get(name, name)


def transform_val(name, val):
    if name in [COST_CC_SUM, CPC_CC, CONVERSIONS_VALUE_CC_SUM]:
        return _transform_cc_to_decimal(val)

    if name in [CTR, BOUNCE_RATE, PERCENT_NEW_USERS, CLICK_DISCREPANCY]:
        return _tranform_percent(val)

    return val


def _transform_cc_to_decimal(val):
    if val is not None:
        return float(decimal.Decimal(round(val)) / decimal.Decimal(10000))


def _tranform_percent(val):
    if val is not None:
        return val * 100
