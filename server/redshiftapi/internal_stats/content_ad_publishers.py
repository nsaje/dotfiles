from redshiftapi import db
from redshiftapi import queries
from collections import namedtuple

import dash.models


def query_content_ad_publishers(date_from, date_to, ad_group_ids=None):
    constraints = {
        'date__gte': date_from,
        'date__lte': date_to,
    }
    if ad_group_ids:
        constraints['ad_group_id'] = ad_group_ids

    sql, params = queries.prepare_query_all_base(
        breakdown=['ad_group_id', 'content_ad_id', 'publisher', 'source_id'],
        constraints=constraints,
        parents=None,
        use_publishers_view=True
    )

    cursor = db.get_stats_cursor()
    cursor.execute(sql, params)
    return _fetch_all_with_source_slug(cursor)


def _fetch_all_with_source_slug(cursor):
    desc = cursor.description
    stats = namedtuple('Stats', [col[0] for col in desc])
    stats_out = namedtuple('StatsOutput', ['source_slug', 'ad_group_id', 'content_ad_id', 'publisher', 'clicks', 'cost', 'dataCost'])

    source_id_map = {s.id: s.bidder_slug for s in dash.models.Source.objects.all()}

    for row in cursor:
        c = stats(*row)
        c_out = stats_out(
            source_slug=source_id_map[c.source_id],
            ad_group_id=c.ad_group_id,
            content_ad_id=c.content_ad_id,
            publisher=c.publisher,
            clicks=c.clicks,
            cost=c.media_cost,
            dataCost=c.data_cost,
        )
        yield c_out
