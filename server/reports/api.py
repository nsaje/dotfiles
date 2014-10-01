from __future__ import division

import datetime
import decimal
import urlparse
import urllib
import logging
import collections
import operator

import pytz

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
from django.db.models import Sum, Min, Max

from . import exc
from . import models

from dash import models as dashmodels
from utils import db_aggregates

logger = logging.getLogger(__name__)

MAX_RECONCILIATION_RETRIES = 10

DIMENSIONS = set(['article', 'ad_group', 'date', 'source', 'account', 'campaign'])

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


def query_stats(start_date, end_date, breakdown=None, **constraints):
    breakdown = _preprocess_breakdown(breakdown)
    constraints = _preprocess_constraints(constraints)

    result = models.ArticleStats.objects

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


def query_goal(start_date, end_date, breakdown=None, **constraints):
    breakdown = _preprocess_breakdown(breakdown)
    breakdown.append('goal_name')
    constraints = _preprocess_constraints(constraints)

    result = models.GoalConversionStats.objects

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


def sorted_results(results, order=None):
    rows = results[:]
    if not order:
        return rows
    for field in reversed(order):
        desc = False
        deco_fun = lambda x: x is None
        if field.startswith('-'):
            desc=True
            field = field[1:]
            deco_fun = lambda x: x is not None
        cmp_fun = lambda w: lambda x, y: cmp((deco_fun(x.get(w)), x.get(w)), (deco_fun(y.get(w)), y.get(w)))
        rows = sorted(rows, cmp=cmp_fun(field), reverse=desc)
    return rows


def query(start_date, end_date, breakdown=None, order=None, **constraints):
    report_results = query_stats(start_date, end_date, breakdown=breakdown, **constraints)
    report_results = _collect_results(report_results)

    conversion_results = query_goal(start_date, end_date, breakdown=breakdown, **constraints)
    conversion_results = _collect_results(conversion_results)
    
    # in memory join of the result sets
    if breakdown:
        # include related data
        if 'article' in breakdown:
            report_results = _include_article_data(report_results)

        global RowKey
        RowKey = collections.namedtuple('RowKey', ' '.join(breakdown))
        results = {}
        for row in report_results:
            key = _extract_key(row, breakdown)
            results[key] = row
        for row in conversion_results:
            key = _extract_key(row, breakdown)
            _extend_result(results[key], row)
        
        for key, row in results.iteritems():
            _add_computed_metrics(row)

        return sorted_results(results.values(), order)
    else:
        # no breakdown => the result is a single row aggregate
        result = report_results
        for row in conversion_results:
            _extend_result(result, row)
        _add_computed_metrics(result)
        return result


def paginate(result, page, page_size):
    paginator = Paginator(result, page_size)

    try:
        result_pg = paginator.page(page)
    except PageNotAnInteger:
        result_pg = paginator.page(1)
    except EmptyPage:
        result_pg = paginator.page(paginator.num_pages)

    return (
        [r for r in result_pg],
        result_pg.number,
        result_pg.paginator.num_pages,
        result_pg.paginator.count,
        result_pg.start_index(),
        result_pg.end_index()
    )


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


def get_yesterday_cost(ad_group):
    today_utc = pytz.UTC.localize(datetime.datetime.utcnow())
    today = today_utc.astimezone(pytz.timezone(settings.TIMEZONE)).replace(tzinfo=None)
    today = datetime.datetime(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)

    rs = query(
        start_date=yesterday,
        end_date=yesterday,
        breakdown=['source'],
        ad_group=ad_group
    )
    result = {row['source']: row['cost'] for row in rs}

    return result


def _has_any_postclick_metrics(**kwargs):
    rs = models.ArticleStats.objects
    if 'ad_groups' in kwargs:
        rs = rs.filter(ad_group__in=kwargs['ad_groups'])
    elif 'campaigns' in kwargs:
        rs = rs.filter(ad_group__campaign__in=kwargs['campaigns'])
    elif 'accounts' in kwargs:
        rs = rs.filter(ad_group__campaign__account__in=kwargs['accounts'])

    rs = rs.aggregate(has_postclick_metrics_max=Max('has_postclick_metrics'))

    return rs['has_postclick_metrics_max'] == 1


def has_complete_postclick_metrics(start_date, end_date, **kwargs):
    if not _has_any_postclick_metrics(**kwargs):
        return True

    rs = models.ArticleStats.objects.filter(
        datetime__gte=start_date,
        datetime__lte=end_date
    )

    if 'ad_groups' in kwargs:
        rs = rs.filter(ad_group__in=kwargs['ad_groups'])
    elif 'campaigns' in kwargs:
        rs = rs.filter(ad_group__campaign__in=kwargs['campaigns'])
    elif 'accounts' in kwargs:
        rs = rs.filter(ad_group__campaign__account__in=kwargs['accounts'])

    rs = rs.values('datetime').annotate(
        has_postclick_metrics_max=Max('has_postclick_metrics')
    )

    is_complete = reduce(operator.iand,
        (r['has_postclick_metrics_max'] == 1 for r in rs),
        True
    )

    return is_complete


def _reset_existing_traffic_stats(ad_group, source, date):
    existing_stats = models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=date)
    if existing_stats:
        logger.info(
            'Resetting {num} old article traffic statistics. Ad_group: {ad_group}, Source: {source}, datetime: {datetime}'
            .format(num=len(existing_stats), ad_group=ad_group, source=source, datetime=date)
        )
        for stats in existing_stats:
            stats.reset_traffic_metrics()


@transaction.atomic
def save_report(ad_group, source, rows, date):
    '''
    looks for the article stats with dimensions specified in this row
    if it does not find, it adds the row
    if it does find, it updates the metrics of the existing row
    '''

    _reset_existing_traffic_stats(ad_group, source, date)

    for row in rows:
        article = _reconcile_article(row['url'], row['title'], ad_group)

        try:
            article_stats = models.ArticleStats.objects.get(
                datetime=date,
                article=article,
                ad_group=ad_group,
                source=source
            )
        except models.ArticleStats.DoesNotExist:
            article_stats = models.ArticleStats(
                datetime=date,
                article=article,
                ad_group=ad_group,
                source=source
            )

        article_stats.impressions += row['impressions']
        article_stats.clicks += row['clicks']

        if 'cost_cc' not in row or row['cost_cc'] is None:
            article_stats.cost_cc += row['cpc_cc'] * row['clicks']
        else:
            article_stats.cost_cc += row['cost_cc']

        article_stats.has_traffic_metrics = 1

        article_stats.save()


# helpers


def _reconcile_article(raw_url, title, ad_group):
    if not ad_group:
        raise exc.ArticleReconciliationException('Missing ad group.')

    if not title:
        raise exc.ArticleReconciliationException('Missing article title.')

    if not raw_url:
        raise exc.ArticleReconciliationException('Missing article url.')

    url, _ = clean_url(raw_url)

    try:
        return dashmodels.Article.objects.get(ad_group=ad_group, title=title, url=url)
    except dashmodels.Article.DoesNotExist:
        pass

    try:
        with transaction.atomic():
            return dashmodels.Article.objects.create(ad_group=ad_group, url=url, title=title)
    except IntegrityError:
        logger.info(
            u'Integrity error upon inserting article: title = {title}, url = {url}, ad group id = {ad_group_id}. '
            u'Using existing article.'.
            format(title=title, url=url, ad_group_id=ad_group.id)
        )
        return dashmodels.Article.objects.get(ad_group=ad_group, url=url, title=title)


def clean_url(raw_url):
    '''
    Removes all utm_* and z1_* params, then alphabetically order the remaining params
    '''
    split_url = list(urlparse.urlsplit(raw_url))
    query_parameters = urlparse.parse_qsl(split_url[3], keep_blank_values=True)

    cleaned_query_parameters = filter(
        lambda (attr, value): not (attr.startswith('utm_') or attr.startswith('_z1_')),
        query_parameters
    )

    split_url[3] = urllib.urlencode(sorted(cleaned_query_parameters, key=lambda x: x[0]))

    return urlparse.urlunsplit(split_url), dict(query_parameters)
