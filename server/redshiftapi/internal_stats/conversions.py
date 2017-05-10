from redshiftapi import db
from redshiftapi import queries
from collections import namedtuple

import dash.models


def query_conversions(date_from, date_to, ad_group_ids=None):
    constraints = {
        'date__gte': date_from,
        'date__lte': date_to,
    }
    if ad_group_ids:
        constraints['ad_group_id'] = ad_group_ids

    sql, params = queries.prepare_query_all_touchpoints(
        breakdown=['ad_group_id', 'publisher', 'source_id'],
        constraints=constraints,
        parents=None,
        use_publishers_view=False
    )

    cursor = db.get_stats_cursor()
    cursor.execute(sql, params)
    return _fetch_all_with_source_slug(cursor)


def _fetch_all_with_source_slug(cursor):
    desc = cursor.description
    conversion = namedtuple('Conversion', [col[0] for col in desc] + ["source_slug"])

    source_id_map = {s.id: s.bidder_slug for s in dash.models.Source.objects.all()}

    for row in cursor:
        c = conversion(*row)
        c.source_slug = source_id_map[row.source_id]
        yield c
