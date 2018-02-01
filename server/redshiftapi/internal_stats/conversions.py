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

    sql, params, temp_tables = queries.prepare_query_all_touchpoints(
        breakdown=['ad_group_id', 'content_ad_id', 'publisher_id', 'publisher', 'source_id', 'slug'],
        constraints=constraints,
        parents=None)

    cursor = db.get_stats_cursor()
    with db.create_temp_tables(cursor, temp_tables):
        cursor.execute(sql, params)
        return _fetch_all_with_source_slug(cursor)


def _fetch_all_with_source_slug(cursor):
    desc = cursor.description
    conversion = namedtuple('Conversion', [col[0] for col in desc])
    conversion_out = namedtuple('ConversionOutput', ['source_slug', 'ad_group_id', 'content_ad_id', 'publisher', 'slug', 'count'])

    source_id_map = {s.id: s.bidder_slug for s in dash.models.Source.objects.all()}

    for row in cursor:
        c = conversion(*row)
        c_out = conversion_out(
            source_slug=source_id_map[c.source_id],
            ad_group_id=c.ad_group_id,
            content_ad_id=c.content_ad_id,
            publisher=c.publisher,
            slug=c.slug,
            count=c.count,
        )
        yield c_out
