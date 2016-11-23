from redshiftapi import db
from redshiftapi import queries


def query_campaign(campaign_id, date_from, date_to):
    sql, params = queries.prepare_query_all_base(
        breakdown=[],
        constraints={
            'campaign_id': campaign_id,
            'date__gte': date_from,
            'date__lte': date_to,
        },
        parents=None,
        use_publishers_view=False
    )

    rows = db.execute_query(sql, params, 'campaign_quick_stats')
    return rows[0]
