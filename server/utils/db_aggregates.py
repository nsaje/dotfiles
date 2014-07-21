from django.db.models import aggregates, sql


class SumDivisionAggregate(sql.aggregates.Aggregate):
    is_ordinal = False
    is_computed = True
    # Not used
    sql_function = 'SUM_DIVISION'
    sql_template = 'CASE WHEN SUM(%(divisor)s) <> 0 THEN SUM(CAST(%(field)s AS FLOAT)) / SUM(%(divisor)s) ELSE NULL END'


class SumDivision(aggregates.Aggregate):
    name = 'SumDivision'

    def __init__(self, col, divisor, **extra):
        super(SumDivision, self).__init__(col, divisor=divisor, **extra)

    def add_to_query(self, query, alias, col, source, is_summary):
        query.aggregates[alias] = SumDivisionAggregate(
            col, source=source, is_summary=is_summary, **self.extra)
