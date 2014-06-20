import datetime

from fakedata import DATA

DIMENSIONS = ['date', 'article', 'ad_group', 'network']
METRICS = ['impressions', 'clicks', 'cost', 'cpc']
COMPUTED_METRICS = {
    'ctr': lambda row: float(row['clicks'])/row['impressions'] if row['impressions'] > 0 else 0
}

def average(vals):
    return float(sum(vals)) / len(vals) if len(vals) > 0 else 0

AGGREGATIONS = {
    'impressions': sum,
    'clicks': sum,
    'cost': sum,
    'cpc': average,
    #'ctr': average,
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
                    grouped_data[key] = {metric:[] for metric in METRICS}
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


# helpers

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
    rows = query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['date'], ad_group=3, network=2)
    print '\n\nresults for:' + "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['date'], ad_group=3, network=2)"
    for row in rows: print row

    # breakdown by date and by network
    rows = query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['date', 'network'], ad_group=3)
    print '\n\nresults for:' + "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['date', 'network'], ad_group=3)"
    for row in rows: print row

    # breakdown by date
    rows = query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['network'], ad_group=1)
    print '\n\nresults for:' + "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=['network'], ad_group=1)"
    for row in rows: print row

    # no breakdown, total values
    rows = query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=[], ad_group=1)
    print '\n\nresults for:' + "query(datetime.date(2014,6,1), datetime.date(2014,6,11), breakdown=[], ad_group=1)"
    for row in rows: print row

