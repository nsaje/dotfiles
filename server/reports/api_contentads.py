import collections

from reports import exc
from reports import models
from reports import aggregate_fields
from reports import api_helpers


def query(start_date, end_date, breakdown=None, **constraints):
    constraints = _preprocess_constraints(constraints)

    stats = models.ContentAdStats.objects.filter(
        date__gte=start_date, date__lte=end_date, **constraints)

    if breakdown:
        breakdown = _preprocess_breakdown(breakdown)
        stats = stats.values(*breakdown).annotate(**aggregate_fields.AGGREGATE_FIELDS)
        return [_transform_row(s) for s in stats]

    stats = stats.aggregate(**aggregate_fields.AGGREGATE_FIELDS)

    return _transform_row(stats)


def _preprocess_breakdown(breakdown):
    if not breakdown or len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    breakdown_field_translate = {
        'ad_group': 'content_ad__ad_group'
    }

    breakdown = [] if breakdown is None else breakdown[:]

    fields = [breakdown_field_translate.get(field, field) for field in breakdown]

    return fields


def _preprocess_constraints(constraints):
    constraint_field_translate = {
        'ad_group': 'content_ad__ad_group',
        'campaign': 'content_ad__ad_group__campaign'
    }

    result = {}
    for k, v in constraints.iteritems():
        k = constraint_field_translate.get(k, k)

        if isinstance(v, collections.Sequence):
            result['{0}__in'.format(k)] = v
        else:
            result[k] = v

    return result


def _transform_row(row):
    result = {}
    for name, val in row.items():
        if name == 'content_ad__ad_group':
            name = 'ad_group'
        else:
            val = aggregate_fields.transform_val(name, val)
            name = aggregate_fields.transform_name(name)

        result[name] = val

    return result
