from __future__ import division

import decimal
import urlparse
import urllib
import logging

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, IntegrityError
from django.db.models import Sum

from . import exc
from . import models

from dash import models as dashmodels
from utils import db_aggregates

logger = logging.getLogger(__name__)

DIMENSIONS = ['date', 'article', 'ad_group', 'source']
METRICS = ['impressions', 'clicks', 'cost', 'cpc']

MAX_RECONCILIATION_RETRIES = 10


# API functions
def query(start_date, end_date, breakdown=None, order=None, page=None, page_size=None, **constraints):
    '''
    api function to query reports data
    start_date = starting date, inclusive
    end_date = end date, inclusive
    order = order by field (eg. 'cpc', '-cpc')
    breakdown = list of dimensions by which to group
    constraints = constraints on the dimension values (e.g. source=x, ad_group=y, etc.)
    '''
    if (page and not page_size) or (page_size and not page):
        raise exc.ReportsQueryError('Missing page or page_size for pagination.')

    if not breakdown:
        breakdown = []
    else:
        # create a copy to ensure that input list is not changed
        breakdown = breakdown[:]

    if not (set(breakdown) <= set(DIMENSIONS)):
        raise exc.ReportsQueryError('Invalid value for breakdown.')

    for i, field in enumerate(breakdown):
        if field == 'date':
            breakdown[i] = 'datetime'
            break

    for k, v in constraints.items():
        if isinstance(v, (list, tuple)):
            new_k = '{0}__in'.format(k)
            constraints[new_k] = v
            del constraints[k]

    current_page = None
    num_pages = None
    count = None
    start_index = None
    end_index = None

    annotate_kwargs = {}
    ordering = breakdown
    order_prop_null = None

    if breakdown:
        order_mapping = {
            'cost': 'cost_cc_sum',
            '-cost': '-cost_cc_sum',
            'impressions': 'impressions_sum',
            '-impressions': '-impressions_sum',
            'clicks': 'clicks_sum',
            '-clicks': '-clicks_sum',
            'ctr': 'ctr',
            '-ctr': '-ctr',
            'cpc': 'cpc',
            '-cpc': '-cpc'
        }

        if order:
            if order not in (order_mapping.keys()):
                raise exc.ReportsQueryError('Invalid value for order.')

            order_prop = order[1:] if order.startswith('-') else order
            # Name of the temporary null property used when ordering to make sure
            # that NULLs alre always at the bottom.
            order_prop_null = '{}_null'.format(order_prop)
            ordering = [order_prop_null, order_mapping[order]]
            annotate_kwargs = {}
            if order_prop == 'cost':
                annotate_kwargs['cost_null'] = db_aggregates.IsSumNull('cost_cc')
            elif order_prop == 'impressions':
                annotate_kwargs['impressions_null'] = \
                    db_aggregates.IsSumNull('impressions')
            elif order_prop == 'clicks':
                annotate_kwargs['clicks_null'] = \
                    db_aggregates.IsSumNull('clicks')
            elif order_prop == 'ctr':
                annotate_kwargs['ctr_null'] = \
                    db_aggregates.IsSumDivisionNull('clicks', divisor='impressions')
            elif order_prop == 'cpc':
                annotate_kwargs['cpc_null'] = \
                    db_aggregates.IsSumDivisionNull('cost_cc', divisor='clicks')

        stats = models.ArticleStats.objects.\
            values(*breakdown).\
            annotate(
                cost_cc_sum=Sum('cost_cc'),
                impressions_sum=Sum('impressions'),
                clicks_sum=Sum('clicks'),
                ctr=db_aggregates.SumDivision('clicks', divisor='impressions'),
                cpc=db_aggregates.SumDivision('cost_cc', divisor='clicks'),
                **annotate_kwargs
            ).\
            filter(**constraints).\
            filter(datetime__gte=start_date, datetime__lte=end_date).\
            order_by(*ordering)

        if page and page_size:
            paginator = Paginator(stats, page_size)

            try:
                stats = paginator.page(page)
            except PageNotAnInteger:
                stats = paginator.page(1)
            except EmptyPage:
                stats = paginator.page(paginator.num_pages)

            current_page = stats.number
            num_pages = stats.paginator.num_pages
            count = stats.paginator.count
            start_index = stats.start_index()
            end_index = stats.end_index()

        stats = list(stats)
    else:
        stats = models.ArticleStats.objects.\
            filter(**constraints).\
            filter(datetime__gte=start_date, datetime__lte=end_date).\
            aggregate(
                cost_cc_sum=Sum('cost_cc'),
                impressions_sum=Sum('impressions'),
                clicks_sum=Sum('clicks'),
                ctr=db_aggregates.SumDivision('clicks', divisor='impressions'),
                cpc=db_aggregates.SumDivision('cost_cc', divisor='clicks'),
            )
        stats = [stats]

    for stat in stats:
        if 'datetime' in stat:
            stat['date'] = stat.pop('datetime').date()

        if stat['cost_cc_sum'] is None:
            stat['cost'] = stat.pop('cost_cc_sum')
        else:
            stat['cost'] = float(decimal.Decimal(round(stat.pop('cost_cc_sum'))) / decimal.Decimal(10000))

        if stat['ctr']:
            stat['ctr'] *= 100

        if stat['cpc']:
            stat['cpc'] = float((decimal.Decimal(stat['cpc']) / decimal.Decimal(10000)))

        stat['impressions'] = stat.pop('impressions_sum')
        stat['clicks'] = stat.pop('clicks_sum')

        if order_prop_null and order_prop_null in stat:
            del stat[order_prop_null]

    return stats, current_page, num_pages, count, start_index, end_index


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

        article_stats = models.ArticleStats(datetime=date, article=article, ad_group=ad_group, source=source)

        article_stats.impressions = row['impressions']
        article_stats.clicks = row['clicks']

        if 'cost_cc' not in row or row['cost_cc'] is None:
            article_stats.cost_cc = row['cpc_cc'] * row['clicks']
        else:
            article_stats.cost_cc = row['cost_cc']

        try:
            article_stats.save()
        except IntegrityError:
            raise exc.ReportsSaveError(
                'Article article_id={article_id} appeared more than once for datetime={datetime}, '
                'ad_group_id={ad_group_id}, source_id={source_id}. Article title={title} and url={url}.'.format(
                    article_id=article.id,
                    url=article.url,
                    title=article.title,
                    datetime=date,
                    ad_group_id=ad_group.id,
                    source_id=source.id
                )
            )


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
