from redshiftapi import db
from redshiftapi import queries


def query_campaign(campaign_id, date_from, date_to):
    sql, params, create_tmp_tables, drop_tmp_tables = queries.prepare_query_all_base(
        breakdown=[],
        constraints={
            'campaign_id': campaign_id,
            'date__gte': date_from,
            'date__lte': date_to,
        },
        parents=None,
        use_publishers_view=False
    )

    rows = db.execute_query(
        sql, params,
        'campaign_quick_stats',
        create_tmp_tables=create_tmp_tables,
        drop_tmp_tables=drop_tmp_tables,
    )
    return rows[0]


def query_adgroup(ad_group_id, date_from, date_to, source_id=None):
    constraints = {
        'ad_group_id': ad_group_id,
        'date__gte': date_from,
        'date__lte': date_to,
    }
    if source_id:
        constraints['source_id'] = source_id
    sql, params, create_tmp_tables, drop_tmp_tables = queries.prepare_query_all_base(
        breakdown=[],
        constraints=constraints,
        parents=None,
        use_publishers_view=False
    )

    rows = db.execute_query(
        sql, params,
        'adgroup_quick_stats',
        create_tmp_tables=create_tmp_tables,
        drop_tmp_tables=drop_tmp_tables,
    )
    return rows[0]
