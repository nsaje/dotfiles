import redshiftapi.api_breakdowns
import redshiftapi.api_dailystats
from stats import permission_filter


def query(user, level, breakdown, metrics, constraints, goals, order, should_use_publishers_view=False):
    rows = redshiftapi.api_dailystats.query(breakdown, metrics, constraints, goals, order, should_use_publishers_view)

    permission_filter.filter_columns_by_permission(user, rows, goals, constraints, level)

    return rows
