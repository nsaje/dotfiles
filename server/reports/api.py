from __future__ import division

import decimal
import urlparse
import urllib
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Sum

from . import exc
from . import models

from dash import models as dashmodels

logger = logging.getLogger(__name__)

DIMENSIONS = ['date', 'article', 'ad_group', 'network']
METRICS = ['impressions', 'clicks', 'cost', 'cpc']

MAX_RECONCILIATION_RETRIES = 10


# API functions

def query(start_date, end_date, breakdown=None, **constraints):
    '''
    api function to query reports data
    start_date = starting date, inclusive
    end_date = end date, inclusive
    breakdown = list of dimensions by which to group
    constraints = constraints on the dimension values (e.g. network=x, ad_group=y, etc.)
    '''
    if not breakdown:
        breakdown = []

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

    if breakdown:
        stats = models.ArticleStats.objects.\
            values(*breakdown).\
            filter(**constraints).\
            filter(datetime__gte=start_date, datetime__lte=end_date).\
            annotate(
                cost_cc=Sum('cost_cc'),
                impressions=Sum('impressions'),
                clicks=Sum('clicks')
            ).\
            order_by(*breakdown)

        stats = list(stats)
    else:
        stats = models.ArticleStats.objects.\
            filter(**constraints).\
            filter(datetime__gte=start_date, datetime__lte=end_date).\
            aggregate(
                cost_cc=Sum('cost_cc'),
                impressions=Sum('impressions'),
                clicks=Sum('clicks')
            )
        stats = [stats]

    for stat in stats:
        if 'datetime' in stat:
            stat['date'] = stat.pop('datetime').date()

        if stat['clicks'] is not None and stat['impressions'] > 0:
            stat['ctr'] = stat['clicks'] / stat['impressions'] * 100
        else:
            stat['ctr'] = None

        if stat['cost_cc'] is not None and stat['clicks'] > 0:
            stat['cpc'] = float((decimal.Decimal(stat['cost_cc']) / decimal.Decimal(stat['clicks'])) / decimal.Decimal(10000))
        else:
            stat['cpc'] = None

        if stat['cost_cc'] is None:
            stat['cost'] = stat.pop('cost_cc')
        else:
            stat['cost'] = float(decimal.Decimal(round(stat.pop('cost_cc'))) / decimal.Decimal(10000))

    return stats


@transaction.atomic
def upsert(data, date):
    '''
    looks for the article stats with dimensions specified in this row
    if it does not find, it adds the row
    if it does find, it updates the metrics of the existing row
    '''
    for network_campaign_key, rows in data:
        ad_group_network = dashmodels.AdGroupNetwork.objects.get(network_campaign_key=network_campaign_key)
        ad_group = ad_group_network.ad_group
        network = ad_group_network.network

        for row in rows:
            article = _reconcile_article(row.get('url'), row.get('title'), ad_group)

            try:
                article_stats = models.ArticleStats.objects.get(datetime=date, article=article,
                                                                ad_group=ad_group, network=network)
            except ObjectDoesNotExist:
                article_stats = models.ArticleStats(datetime=date, article=article,
                                                    ad_group=ad_group, network=network)

            if 'cost_cc' not in row or row['cost_cc'] is None:
                row['cost_cc'] = row['cpc_cc'] * row['clicks']

            article_stats.impressions = row['impressions']
            article_stats.clicks = row['clicks']
            article_stats.cost_cc = row['cost_cc']

            article_stats.save()


# helpers


def _reconcile_article(raw_url, title, ad_group):
    if not ad_group:
        raise exc.ArticleReconciliationException('Missing ad group.')

    if not title:
        raise exc.ArticleReconciliationException('Missing article title.')

    article_reconciled, retries = False, 0
    while not article_reconciled and retries < MAX_RECONCILIATION_RETRIES:
        retries += 1

        kwargs = {
            'ad_group': ad_group
        }

        url = None
        if raw_url:
            url = _clean_url(raw_url)
            kwargs['url'] = url

        kwargs['title'] = title

        articles = dashmodels.Article.objects.filter(**kwargs)
        if articles:
            article = articles.latest()
        else:
            try:
                with transaction.atomic():
                    article = dashmodels.Article.objects.create(ad_group=ad_group, url=url, title=title)
            except IntegrityError:
                logger.info(
                    'IntegrityError upon saving new article. url: {url}, '
                    'title: {title}, ad_group_id: {ad_group_id}, # of attempts: '.format(
                        url=url,
                        title=title,
                        ad_group_id=ad_group.id,
                        retries=retries,
                    )
                )
                continue

        article_reconciled = True

    if not article_reconciled:
        raise exc.ArticleReconciliationException('Couldn\'t reconcile article')

    return article


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
