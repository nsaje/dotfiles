import backtosql
import redshiftapi.db

import model


COUNTRY = 'country'
PUBLISHER = 'publisher'
DEVICE_TYPE = 'device_type'
VALID_BREAKDOWNS = (None, COUNTRY, PUBLISHER, DEVICE_TYPE)


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
            'breakdown': [m.get_column(breakdown)] if breakdown else [],
            'aggregates': m.select_columns(group='aggregates'),
            'constraints': q,
            'orders': [m.bid_reqs.as_order('-', nulls='last')],
        }
    )
    params = q.get_params()

    return redshiftapi.db.execute_query(sql, params, query_name='inventory_planning', cache_name='inventory_planning')
