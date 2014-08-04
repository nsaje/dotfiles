from __future__ import division

import datetime
import decimal
import urlparse
import urllib
import logging
import collections

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
from django.db.models import Sum

from . import exc
from . import models

from dash import models as dashmodels
from utils import db_aggregates

logger = logging.getLogger(__name__)

MAX_RECONCILIATION_RETRIES = 10

DIMENSIONS = set(['article', 'ad_group', 'date', 'source'])

AGGREGATE_FIELDS = dict(
    clicks_sum=Sum('clicks'),
    impressions_sum=Sum('impressions'),
    cost_cc_sum=Sum('cost_cc'),
    ctr=db_aggregates.SumDivision('clicks', 'impressions'),
    cpc_cc=db_aggregates.SumDivision('cost_cc', 'clicks')
)


def _preprocess_constraints(constraints):
    result = {}
    for k, v in constraints.iteritems():
        if isinstance(v, collections.Sequence):
            result['{0}__in'.format(k)] = v
        else:
            result[k] = v
    return result


def _preprocess_order(order):
    order_field_translate = {
        'title': 'article__title',
        'cost': 'cost_cc_sum',
        'cpc': 'cpc_cc',
        'clicks': 'clicks_sum',
        'impressions': 'impressions_sum',
        'ctr': 'ctr',
        'date': 'datetime',
        'url': 'article__url'
    }
    order = [] if order is None else order[:]
    result = []
    for x in order:
        is_reverse = False
        if x.startswith('-'):
            is_reverse = True
            x = x[1:]
        new_order_name = order_field_translate.get(x, x)
        if is_reverse:
            new_order_name = '-' + new_order_name
        result.append(new_order_name)
    return result


def _preprocess_breakdown(breakdown):
    breakdown_field_translate = {'date': 'datetime'}
    breakdown = [] if breakdown is None else breakdown[:]
    if len(set(breakdown) - DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')
    fields = [breakdown_field_translate.get(field, field) for field in breakdown]
    return fields


def _add_helper_order_aggregate_fields(agg_fields, order):
    more_agg_fields = {k:v for k,v in agg_fields.items()}
    null_order_fields = []
    for order_field in order:
        if 'clicks_sum' in order_field:
            more_agg_fields['clicks_sum_null'] = db_aggregates.IsSumNull('clicks')
            null_order_fields.append('clicks_sum_null')
        if 'impressions_sum' in order_field:
            more_agg_fields['impressions_sum_null'] = db_aggregates.IsSumNull('impressions')
            null_order_fields.append('impressions_sum_null')
        if 'cost_cc_sum' in order_field:
            more_agg_fields['cost_cc_sum_null'] = db_aggregates.IsSumNull('cost_cc')
            null_order_fields.append('cost_cc_sum_null')
        if 'ctr' in order_field:
            more_agg_fields['ctr_null'] = db_aggregates.IsSumDivisionNull('clicks', 'impressions')
            null_order_fields.append('ctr_null')
        if 'cpc_cc' in order_field:
            more_agg_fields['cpc_cc_null'] = db_aggregates.IsSumDivisionNull('cost_cc', 'clicks')
            null_order_fields.append('cpc_cc_null')
    return more_agg_fields, null_order_fields + order


def _get_own_order(order):
    '''
    returns order_by criteria which apply only to ArticleStats
    '''
    own_order_fields = DIMENSIONS.union(set(['cost_cc_sum', 'cpc_cc', 'clicks_sum', 'impressions_sum', 'ctr', 'datetime']))
    null_helpers = set(['{0}_null'.format(x) for x in own_order_fields])
    own_order_fields = own_order_fields.union(null_helpers)
    result = []
    for x in order:
        colname = x
        if x.startswith('-'):
            colname = x[1:]
        if colname in own_order_fields:
            result.append(x)
    return result


def _include_article_data(rows, order):
    rows = list(rows)
    article_ids = [row['article'] for row in rows]
    article_lookup = {a.pk:a for a in dashmodels.Article.objects.filter(pk__in=article_ids)}
    for row in rows:
        a = article_lookup[row['article']]
        row['article__title'] = a.title
        row['article__url'] = a.url
    article_order = [x for x in order if 'article__title' in x or 'article__url' in x]
    for x in article_order:
        is_reverse = False
        field = x
        if x.startswith('-'):
            field = x[1:]
            is_reverse = True
        rows = sorted(rows, key=lambda row: row[field], reverse=is_reverse)
    return rows


def query(start_date, end_date, breakdown=None, order=None, **constraints):
    breakdown = _preprocess_breakdown(breakdown)
    order = _preprocess_order(order)
    constraints = _preprocess_constraints(constraints)

    result = models.ArticleStats.objects

    result = result.filter(datetime__gte=start_date, datetime__lte=end_date)
    if constraints:
        result = result.filter(**constraints)

    if breakdown:
        result = result.values(*breakdown)
        agg_fields, order = _add_helper_order_aggregate_fields(AGGREGATE_FIELDS, order)
        result = result.annotate(**agg_fields)
    else:
        return result.aggregate(**AGGREGATE_FIELDS)

    if order:
        # only order by fields that are columns in ArticleStats table
        result = result.order_by(*_get_own_order(order))

    if 'article' in breakdown:
        result = _include_article_data(result, order)    # much faster than doing the join

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
        result_pg,
        result_pg.number,
        result_pg.paginator.num_pages,
        result_pg.paginator.count,
        result_pg.start_index(),
        result_pg.end_index()
    )


def collect_results(result):
    col_name_translate = {
        'clicks_sum': 'clicks',
        'impressions_sum': 'impressions',
        'cost_cc_sum': 'cost',
        'cpc_cc': 'cpc',
        'datetime': 'date',
        'article__title': 'title',
        'article__url': 'url',
    }

    col_val_transform = {
        'cost_cc_sum': lambda x: None if x is None else float(decimal.Decimal(round(x)) / decimal.Decimal(10000)),
        'cpc_cc': lambda x: None if x is None else float(decimal.Decimal(round(x)) / decimal.Decimal(10000)),
        'ctr': lambda x: None if x is None else x * 100,
        'datetime': lambda dt: dt.date(),
    }

    def collect_row(row):
        new_row = {}
        for col_name, col_val in dict(row).items():
            if col_name.endswith('_null'):
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
    today = datetime.datetime.utcnow()
    today = datetime.datetime(today.year, today.month, today.day)
    yesterday = today - datetime.timedelta(days=1)

    qs = query(
        start_date=yesterday,
        end_date=yesterday,
        breakdown=['source'],
        ad_group=ad_group
    )
    result = {row['source']: row['cost'] for row in collect_results(qs)}

    return result


def _delete_existing_stats(ad_group, source, date):
    existing_stats = models.ArticleStats.objects.filter(ad_group=ad_group, source=source, datetime=date)
    if existing_stats:
        logger.info(
            'Deleting {num} old article statistics. Ad_group: {ad_group}, Source: {source}, datetime: {datetime}'
            .format(num=len(existing_stats), ad_group=ad_group, source=source, datetime=date)
        )
        existing_stats.delete()


@transaction.atomic
def save_report(ad_group, source, rows, date):
    '''
    looks for the article stats with dimensions specified in this row
    if it does not find, it adds the row
    if it does find, it updates the metrics of the existing row
    '''

    _delete_existing_stats(ad_group, source, date)

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

        article_stats.save()


# helpers


def _reconcile_article(raw_url, title, ad_group):
    if not ad_group:
        raise exc.ArticleReconciliationException('Missing ad group.')

    if not title:
        raise exc.ArticleReconciliationException('Missing article title.')

    if not raw_url:
        raise exc.ArticleReconciliationException('Missing article url.')

    url = _clean_url(raw_url)

    try:
        return dashmodels.Article.objects.get(ad_group=ad_group, title=title, url=url)
    except dashmodels.Article.DoesNotExist:
        pass

    try:
        with transaction.atomic():
            return dashmodels.Article.objects.create(ad_group=ad_group, url=url, title=title)
    except IntegrityError:
        logger.info(
            'Integrity error upon inserting article: title = {title}, url = {url}, ad group id = {ad_group_id}. '
            'Using existing article.'.
            format(title=title, url=url, ad_group_id=ad_group.id)
        )
        return dashmodels.Article.objects.get(ad_group=ad_group, url=url, title=title)


def _clean_url(raw_url):
    '''
    Removes all utm_* params with values starting with zemantaone
    '''
    split_url = list(urlparse.urlsplit(raw_url))
    query_parameters = urlparse.parse_qsl(split_url[3], keep_blank_values=True)

    cleaned_query_parameters = filter(
        lambda (attr, value): not attr.startswith('utm_') or not value.startswith('zemantaone'),
        query_parameters
    )

    split_url[3] = urllib.urlencode(cleaned_query_parameters)

    return urlparse.urlunsplit(split_url)
