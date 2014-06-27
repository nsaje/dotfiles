import datetime
import urlparse
import urllib

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction

from . import exc
from . import models
from .fakedata import DATA

from dash import models as dashmodels

DIMENSIONS = ['date', 'article', 'ad_group', 'network']
METRICS = ['impressions', 'clicks', 'cost', 'cpc']
COMPUTED_METRICS = {
    'ctr': lambda row: float(row['clicks']) / row['impressions'] if row['impressions'] > 0 else 0
}


def average(vals):
    return float(sum(vals)) / len(vals) if len(vals) > 0 else 0

AGGREGATIONS = {
    'impressions': sum,
    'clicks': sum,
    'cost': sum,
    'cpc': average,
    # 'ctr': average,
}


# API functions

def query(start_date, end_date, breakdown=[], **constraints):
    '''
    api function to query reports data
    start_date = starting date, inclusive
    end_date = end date, exclusive
    breakdown = list of dimensions by which to group
    constraints = constraints on the dimension values (e.g. network=x, ad_group=y, etc.)
    '''
    grouped_data = {}

    for row in DATA:
        if row['date'] >= start_date and row['date'] < end_date:
            if _satisfies_constraints(row, constraints):

                key = _get_group_tuple(row, breakdown)
                if key not in grouped_data:
                    grouped_data[key] = {metric: [] for metric in METRICS}
                # add metrics
                for metric in METRICS:
                    grouped_data[key][metric].append(row[metric])

    aggregated_data = {}
    for group_key, metricvals in grouped_data.iteritems():
        agg_metrics = {}
        for metric, values in metricvals.iteritems():
            agg_metrics[metric] = AGGREGATIONS[metric](values)
        aggregated_data[group_key] = agg_metrics

    result = []
    for group_key in sorted(aggregated_data.keys()):
        agg_metrics = aggregated_data[group_key]
        row = {}
        for dimension, val in zip(breakdown, group_key):
            row[dimension] = val
        for metric, val in agg_metrics.iteritems():
            row[metric] = val
        # add computed metrics
        for metric, fun in COMPUTED_METRICS.iteritems():
            row[metric] = fun(row)
        result.append(row)

    return result


def upsert(row):
    '''
    looks for the article stats with dimensions specified in this row
    if it does not find, it adds the row
    if it does find, it updates the metrics of the existing row
    '''
    data = _find_row(row)
    print data
    if not data:
        # data with this dimensions does not exist, we insert it
        DATA.append(row)
    else:
        # data with this dimensions already exists, we update the metrics
        for metric in METRICS:
            data[metric] = row[metric]


def save_article_stats(rows, ad_group, network, date):
    for row in rows:
        with transaction.atomic():
            article = _reconcile_article(row.get('url'), row.get('title'), ad_group)

            try:
                article_stats = models.ArticleStats.objects.get(datetime=date, article=article,
                                                                adgroup=ad_group, network=network)
            except ObjectDoesNotExist:
                article_stats = models.ArticlesStats(datetime=date, article=article,
                                                     ad_group=ad_group, network=network)

            article_stats.impressions = row['impressions']
            article_stats.clicks = row['clicks']
            article_stats.cpc = row['cpc_cc'] / 10000
            article_stats.cost = row['cost_cc'] / 10000
            article_stats.save()


# helpers

@transaction.atomic
def _reconcile_article(raw_url, title, ad_group):
    if not (raw_url or title):
        raise exc.ArticleReconciliationException('Missing both URL and title.')

    kwargs = {
        'ad_group': ad_group
    }

    url = _clean_url(raw_url)

    if url:
        kwargs['url'] = url
    else:
        kwargs['title'] = title

    try:
        article = dashmodels.Article.objects.get(**kwargs)
    except ObjectDoesNotExist:
        article = dashmodels.Article.create(ad_group=ad_group, url=url, title=title)
    except MultipleObjectsReturned:
        raise exc.ArticleReconciliationException(
            'Mutlitple objects returned for arguments: {kwargs}.'.format(kwargs=kwargs)
        )

    if title and title != article.title:
        article.title = title
        article.save()

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


def _satisfies_constraints(row, constraints):
    for dimension, value in constraints.iteritems():
        if row[dimension] != value:
            return False
    return True


def _get_group_tuple(row, breakdown):
    dimvals = [row[dimension] for dimension in breakdown]
    return tuple(dimvals)


def _find_row(row):
    for data in DATA:
        found = True
        for dimension in DIMENSIONS:
            if data[dimension] != row[dimension]:
                found = False
                break
        if found:
            return data
    return None


if __name__ == '__main__':
    # breakdown by date
    rows = query(datetime.date(2014, 6, 1), datetime.date(2014, 6, 11), breakdown=['date'], ad_group=3, network=2)
    print '\n\nresults for:'\
          "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['date'], ad_group=3, network=2)"
    for row in rows:
        print row

    # breakdown by date and by network
    rows = query(datetime.date(2014, 6, 1), datetime.date(2014, 6, 11), breakdown=['date', 'network'], ad_group=3)
    print '\n\nresults for:'\
          "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['date', 'network'], ad_group=3)"
    for row in rows:
        print row

    # breakdown by date
    rows = query(datetime.date(2014, 6, 1), datetime.date(2014, 6, 11), breakdown=['network'], ad_group=1)
    print '\n\nresults for:'\
          "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['network'], ad_group=1)"
    for row in rows:
        print row

    # no breakdown, total values
    rows = query(datetime.date(2014, 6, 1), datetime.date(2014, 6, 11), breakdown=[], ad_group=1)
    print '\n\nresults for:'\
          "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=[], ad_group=1)"
    for row in rows:
        print row
