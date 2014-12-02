from __future__ import division

import datetime
import decimal
import logging
import collections

import pytz

from django.conf import settings
from django.db.models import Sum, Min, Max

from . import exc
from . import models

from dash import models as dashmodels
from utils import db_aggregates
from utils.sort_helper import sort_results

logger = logging.getLogger(__name__)


DIMENSIONS = set(['article', 'ad_group', 'date', 'source', 'account', 'campaign'])
TRAFFIC_FIELDS = ['clicks', 'impressions', 'cost', 'cpc', 'ctr', 'title', 'url']
POSTCLICK_FIELDS = [
    'visits', 'percent_new_users', 'pv_per_visit', 'avg_tos',
    'bounce_rate', 'goals', 'click_discrepancy', 'pageviews',
]

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
    percent_new_users=db_aggregates.SumDivision('new_visits', 'visits'),
    bounce_rate=db_aggregates.SumDivision('bounced_visits', 'visits'),
    pageviews_sum=Sum('pageviews'),
    pv_per_visit=db_aggregates.SumDivision('pageviews', 'visits'),
    avg_tos=db_aggregates.SumDivision('duration', 'visits'),
)

GOAL_AGGREGATE_FIELDS = dict(
    conversions_sum=Sum('conversions'),
    conversions_value_cc_sum=Sum('conversions_value_cc'),
)


def _preprocess_constraints(constraints):
    constraint_field_translate = {
        'account': 'ad_group__campaign__account',
        'campaign': 'ad_group__campaign'
    }
    result = {}
    for k, v in constraints.iteritems():
        k = constraint_field_translate.get(k, k)
        if isinstance(v, collections.Sequence):
            result['{0}__in'.format(k)] = v
        else:
            result[k] = v
    return result


def _preprocess_breakdown(breakdown):
    breakdown_field_translate = {
        'date': 'datetime',
        'account': 'ad_group__campaign__account',
        'campaign': 'ad_group__campaign'
    }
    breakdown = [] if breakdown is None else breakdown[:]
    if len(set(breakdown) - DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')
    fields = [breakdown_field_translate.get(field, field) for field in breakdown]
    return fields


def _include_article_data(rows):
    rows = list(rows)
    article_ids = [row['article'] for row in rows]
    article_lookup = {a.pk:a for a in dashmodels.Article.objects.filter(pk__in=article_ids)}
    for row in rows:
        a = article_lookup[row['article']]
        row['title'] = a.title
        row['url'] = a.url
    return rows


def _get_initial_qs(breakdown, **constraints):
    qs = models.ArticleStats.objects
    if settings.QUERY_AGGREGATE_REPORTS and 'article' not in breakdown \
        and 'article' not in constraints and 'article__in' not in constraints:
        qs = models.AdGroupStats.objects
    return qs


def query_stats(start_date, end_date, breakdown=None, **constraints):
    breakdown = _preprocess_breakdown(breakdown)
    constraints = _preprocess_constraints(constraints)

    result = _get_initial_qs(breakdown, **constraints)

    result = result.filter(datetime__gte=start_date, datetime__lte=end_date)
    if constraints:
        result = result.filter(**constraints)

    agg_fields = {k:v for k, v in list(AGGREGATE_FIELDS.items()) + list(POSTCLICK_AGGREGATE_FIELDS.items())}

    if breakdown:
        result = result.values(*breakdown)
        result = result.annotate(**agg_fields)
    else:
        result = result.aggregate(**agg_fields)

    return result


def _get_initial_conversion_qs(breakdown, **constraints):
    qs = models.GoalConversionStats.objects
    if settings.QUERY_AGGREGATE_REPORTS and 'article' not in breakdown \
        and 'article' not in constraints and 'article__in' not in constraints:
        qs = models.AdGroupGoalConversionStats.objects
    return qs


def query_goal(start_date, end_date, breakdown=None, **constraints):
    breakdown = _preprocess_breakdown(breakdown)
    breakdown.append('goal_name')
    constraints = _preprocess_constraints(constraints)

    result = _get_initial_conversion_qs(breakdown)

    result = result.filter(datetime__gte=start_date, datetime__lte=end_date)
    if constraints:
        result = result.filter(**constraints)

    if breakdown:
        result = result.values(*breakdown)
        result = result.annotate(**GOAL_AGGREGATE_FIELDS)

    return result


def _extract_key(result, breakdown):
    values = [result[field] for field in breakdown]
    return RowKey(*values)


def _extend_result(result, conversion_result):
    goal_name = conversion_result['goal_name']
    conversions = conversion_result['conversions']
    conversion_value = conversion_result['conversion_value']
    goals = result.get('goals', {})
    this_goal = goals.get(goal_name, {})
    this_goal['conversions'] = conversions
    this_goal['conversion_value'] = conversion_value
    goals[goal_name] = this_goal
    result['goals'] = goals


def _add_computed_metrics(result):
    if result.get('clicks') is None or result.get('visits') is None or result['clicks'] == 0:
        result['click_discrepancy'] = None
    else:
        result['click_discrepancy'] =  100.0 * max(0, result['clicks'] - result['visits']) / result['clicks']
 
    for goal_name, metrics in result.get('goals', {}).iteritems():
        metrics['conversion_rate'] = metrics['conversions'] / result['visits'] if result['visits'] > 0 else None

    if result['visits'] == 0:
        result['visits'] = None
        result['pageviews'] = None
        result['bounce_rate'] = None
        result['percent_new_users'] = None
        result['pv_per_visit'] = None
        result['avg_tos'] = None
        result['click_discrepancy'] = None

        for goal_name, metrics in result.get('goals', {}).iteritems():
            for metric_name in metrics:
                metrics[metric_name] = None


def _get_report_results(start_date, end_date, breakdown=None, **constraints):
    report_results = query_stats(start_date, end_date, breakdown=breakdown, **constraints)
    report_results = _collect_results(report_results)

    if breakdown and 'article' in breakdown:
        report_results = _include_article_data(report_results)

    return report_results


def _get_conversion_results(start_date, end_date, breakdown=None, **constraints):
    conversion_results = query_goal(start_date, end_date, breakdown=breakdown, **constraints)
    conversion_results = _collect_results(conversion_results)
    return conversion_results


def _join_with_conversions(breakdown, report_results, conversion_results):
    if not breakdown:
        # no breakdown => the result is a single row aggregate
        result = report_results
        for row in conversion_results:
            _extend_result(result, row)
        _add_computed_metrics(result)
        return result

    global RowKey
    RowKey = collections.namedtuple('RowKey', ' '.join(breakdown))
    results = {}
    for row in report_results:
        key = _extract_key(row, breakdown)
        results[key] = row
    for row in conversion_results:
        key = _extract_key(row, breakdown)
        if key in results:
            _extend_result(results[key], row)
    for key, row in results.iteritems():
        _add_computed_metrics(row)
    return results.values()


def query(start_date, end_date, breakdown=None, order=None, **constraints):
    report_results = _get_report_results(start_date, end_date, breakdown, **constraints)
    conversion_results = _get_conversion_results(start_date, end_date, breakdown, **constraints)
    results = _join_with_conversions(breakdown, report_results, conversion_results)
    results = sort_results(results, order)
    return results


def count_reports_rows(start_date, end_date, **constraints):
    return models.ArticleStats.objects.filter(
        datetime__gte=start_date,
        datetime__lte=end_date,
        **constraints
    ).count()


def filter_by_permissions(result, user):
    '''
    filters reports such that the user will only get fields that he is allowed to see
    '''
    def filter_row(row):
        filtered_row = {}
        for field in DIMENSIONS:
            if field in row:
                filtered_row[field] = row[field]
        for field in TRAFFIC_FIELDS:
            if field in row:
                filtered_row[field] = row[field]
        if user.has_perm('zemauth.postclick_metrics'):
            for field in POSTCLICK_FIELDS:
                if field in row:
                    filtered_row[field] = row[field]
        return filtered_row
    if isinstance(result, dict):
        return filter_row(result)
    else:
        return [filter_row(row) for row in result]


def _collect_results(result):
    col_name_translate = {
        'clicks_sum': 'clicks',
        'impressions_sum': 'impressions',
        'cost_cc_sum': 'cost',
        'cpc_cc': 'cpc',
        'datetime': 'date',
        'ad_group__campaign': 'campaign',
        'ad_group__campaign__account': 'account',

        'visits_sum': 'visits',
        'new_visits_sum': 'new_visits',
        'pageviews_sum': 'pageviews',
        'conversions_value_cc_sum': 'conversion_value',
        'conversions_sum': 'conversions'
    }

    col_val_transform = {
        'cost_cc_sum': lambda x: None if x is None else float(decimal.Decimal(round(x)) / decimal.Decimal(10000)),
        'cpc_cc': lambda x: None if x is None else float(decimal.Decimal(round(x)) / decimal.Decimal(10000)),
        'ctr': lambda x: None if x is None else x * 100,
        'datetime': lambda dt: dt.date(),
        'conversions_value_cc_sum': lambda x: None if x is None else float(decimal.Decimal(round(x)) / decimal.Decimal(10000)),
        'bounce_rate': lambda x: None if x is None else x * 100,
        'percent_new_users': lambda x: None if x is None else x * 100,
    }

    def collect_row(row):
        new_row = {}
        for col_name, col_val in dict(row).items():
            if col_name.endswith('_null') or col_name.endswith('_metrics_min') or col_name.endswith('_metrics_max'):
                continue
            new_col_val = col_val_transform.get(col_name, lambda x: x)(col_val)
            new_col_name = col_name_translate.get(col_name, col_name)
            new_row[new_col_name] = new_col_val

        return new_row

    if isinstance(result, dict):
        return collect_row(result)
    else:
        return [collect_row(row) for row in result]


def get_yesterday_cost(**constraints):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).replace(tzinfo=None)
    today = datetime.datetime(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)

    rs = query(
        start_date=yesterday,
        end_date=yesterday,
        breakdown=['source'],
        **constraints
    )
    result = {row['source']: row['cost'] for row in rs}

    return result


def has_complete_postclick_metrics_accounts(start_date, end_date, accounts):
    return _has_complete_postclick_metrics(
        start_date,
        end_date,
        'ad_group__campaign__account',
        accounts
    )


def has_complete_postclick_metrics_campaigns(start_date, end_date, campaigns):
    return _has_complete_postclick_metrics(
        start_date,
        end_date,
        'ad_group__campaign',
        campaigns
    )


def has_complete_postclick_metrics_ad_groups(start_date, end_date, ad_groups):
    return _has_complete_postclick_metrics(
        start_date,
        end_date,
        'ad_group',
        ad_groups
    )


def row_has_traffic_data(row):
    return any(row.get(field) is not None for field in TRAFFIC_FIELDS)


def row_has_postclick_data(row):
    return any(row.get(field) is not None for field in POSTCLICK_FIELDS)


def _get_ad_group_ids_with_postclick_data(key, objects):
    """
    Filters the objects that are passed in and returns ids
    of only those that have any postclick metric data in ArticleStats.
    """
    kwargs = {}
    kwargs[key + '__in'] = objects

    queryset = _get_initial_qs([])

    queryset = queryset.filter(**kwargs).values('ad_group').annotate(
        has_any_postclick_metrics=Max('has_postclick_metrics')
    ).filter(has_any_postclick_metrics=1)

    return [item['ad_group'] for item in queryset]


def _has_complete_postclick_metrics(start_date, end_date, key, objects):
    """
    Returns True if passed-in objects have complete postclick data for the
    specfied date range. All objects that don't have this data at all are ignored.
    """
    ids = _get_ad_group_ids_with_postclick_data(key, objects)

    if len(ids) == 0:
        return True

    queryset = _get_initial_qs([])

    aggr = queryset.filter(
        datetime__gte=start_date,
        datetime__lte=end_date,
        ad_group__in=ids
    ).values('datetime', 'ad_group').\
        annotate(has_any_postclick_metrics=Max('has_postclick_metrics')).\
        aggregate(has_all_postclick_metrics=Min('has_any_postclick_metrics'))

    return aggr['has_all_postclick_metrics'] == 1


def _reset_existing_traffic_stats(ad_group, source, date):
    existing_stats = models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=date)
    if existing_stats:
        logger.info(
            'Resetting {num} old article traffic statistics. Ad_group: {ad_group}, Source: {source}, datetime: {datetime}'
            .format(num=len(existing_stats), ad_group=ad_group, source=source, datetime=date)
        )
        for stats in existing_stats:
            stats.reset_traffic_metrics()
