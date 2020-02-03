from django.conf import settings

import backtosql
import redshiftapi.db

from . import model

COUNTRY = "country"
PUBLISHER = "publisher"
DEVICE_TYPE = "device_type"
SOURCE_ID = "source_id"
VALID_BREAKDOWNS = (None, COUNTRY, PUBLISHER, DEVICE_TYPE, SOURCE_ID)


def query(breakdown=None, constraints=None):
    constraints = constraints or {}
    assert breakdown in VALID_BREAKDOWNS
    if constraints:
        for field in list(constraints.keys()):
            assert field in VALID_BREAKDOWNS

    m = model.Inventory()
    q = backtosql.Q(m, **constraints)

    sql = backtosql.generate_sql(
        "inventory_planning.sql",
        {
            "breakdown": [m.get_column(breakdown)] if breakdown else [],
            "aggregates": m.select_columns(group="aggregates"),
            "constraints": q,
            "orders": [m.bid_reqs.as_order("-", nulls="last")],
        },
    )
    params = q.get_params()

    return redshiftapi.db.execute_query(
        sql,
        params,
        query_name="inventory_planning",
        cache_name="inventory_planning",
        db_cluster=settings.STATS_DB_HOT_CLUSTER,
    )


def query_top_publishers(breakdown=None, constraints=None):
    result = redshiftapi.db.execute_query(
        "SELECT DISTINCT publisher FROM mv_inventory GROUP BY publisher ORDER BY SUM(bids) DESC LIMIT 20000",
        params=None,
        query_name="inventory_planning_publisher_names",
        cache_name="inventory_planning",
    )
    return [row["publisher"] for row in result]
