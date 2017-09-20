import backtosql
import redshiftapi.db

import model


COUNTRY = 'country'
PUBLISHER = 'publisher'
DEVICE_TYPE = 'device_type'
VALID_BREAKDOWNS = (None, COUNTRY, PUBLISHER, DEVICE_TYPE)
AGGREGATE_COLUMNS = ('bid_reqs', 'bids', 'win_notices', 'total_win_price')


def query(breakdown=None, constraints=None):
    constraints = constraints or {}
    assert breakdown in VALID_BREAKDOWNS
    if constraints:
        for field in constraints.keys():
            assert field in VALID_BREAKDOWNS

    m = model.Inventory()
    q = backtosql.Q(m, **constraints)

    sql = backtosql.generate_sql(
        'inventory_planning.sql',
        {
            'breakdown': m.select_columns(subset=[breakdown] if breakdown else []),
            'aggregates': m.select_columns(AGGREGATE_COLUMNS),
            'constraints': q
        }
    )
    params = q.get_params()

    return redshiftapi.db.execute_query(sql, params, query_name='inventory_planning', cache_name='inventory_planning')
