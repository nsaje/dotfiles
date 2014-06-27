import decimal

from django.db.models import Avg, Sum

import models

from fakedata import DATA

DIMENSIONS = ['date', 'article', 'ad_group', 'network']
METRICS = ['impressions', 'clicks', 'cost', 'cpc']


class ReportsQueryError(Exception):
    '''
    Base error. If implementing custom errors, subclass this error.
    '''
    def __init__(self, message=None):
        super(ReportsQueryError, self).__init__(message)


# API functions

def query(start_date, end_date, breakdown=None, **constraints):
    '''
    api function to query reports data
    start_date = starting date, inclusive
    end_date = end date, exclusive
    breakdown = list of dimensions by which to group
    constraints = constraints on the dimension values (e.g. network=x, ad_group=y, etc.)
    '''
    if not breakdown:
        breakdown = []

    if not (set(breakdown) <= set(DIMENSIONS)):
        raise ReportsQueryError('Invalid value for breakdown.')

    if 'date' not in breakdown:
        breakdown.insert(0, 'datetime')
    else:
        for i, field in enumerate(breakdown):
            if field == 'date':
                breakdown[i] = 'datetime'
                break

    for k, v in constraints.items():
        if isinstance(v, (list, tuple)):
            new_k = '{0}__in'.format(k)
            constraints[new_k] = v
            del constraints[k]

    stats = models.ArticleStats.objects.\
            values(*breakdown).\
            filter(**constraints).\
            annotate(
                cpc_cc=Avg('cpc_cc'),
                cost_cc=Avg('cost_cc'),
                impressions=Sum('impressions'),
                clicks=Sum('clicks')
            ).\
            order_by(*breakdown)

    stats = list(stats)

    for stat in stats:
        stat['date'] = stat.pop('datetime').date()
        stat['ctr'] = float(stat['clicks']) / stat['impressions'] if stat['impressions'] > 0 else None
        stat['cost'] = float(decimal.Decimal(round(stat.pop('cost_cc'))) / decimal.Decimal(10000))
        stat['cpc'] = float(decimal.Decimal(round(stat.pop('cpc_cc'))) / decimal.Decimal(10000))

    return stats


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


# helpers

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
