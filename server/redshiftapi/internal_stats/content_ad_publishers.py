import backtosql
from redshiftapi import db
from redshiftapi import models as rsmodels
from collections import namedtuple

import dash.models


def query_content_ad_publishers(date_from, date_to, ad_group_ids=None):
    constraints = {
        'date__gte': date_from,
        'date__lte': date_to,
    }
    if ad_group_ids:
        constraints['ad_group_id'] = ad_group_ids

    mvmaster = rsmodels.MVMasterPublishers()
    breakdown = ['ad_group_id', 'content_ad_id', 'publisher', 'source_id']
    context = {
        'breakdown': mvmaster.select_columns(breakdown),
        'aggregates': [x for x in mvmaster.get_aggregates() if x.alias != 'external_id'],  # this is some special publishers view column
        'constraints': mvmaster.get_constraints(constraints, None),
        'view': 'mv_master',
        'orders': [mvmaster.get_column('-clicks').as_order('-clicks', nulls='last')],
    }

    sql = backtosql.generate_sql('breakdown.sql', context)
    params = context['constraints'].get_params()
    cursor = db.get_stats_cursor()
    cursor.execute(sql, params)
    return _fetch_all_with_source_slug(cursor)


def _fetch_all_with_source_slug(cursor):
    desc = cursor.description
    stats = namedtuple('Stats', [col[0] for col in desc])
    stats_out = namedtuple('StatsOutput', ['source_slug', 'ad_group_id', 'content_ad_id', 'publisher', 'clicks', 'media_cost', 'data_cost', 'video_complete'])

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
            data_cost=c.data_cost,
            video_complete=c.video_complete,
        )
        yield c_out
