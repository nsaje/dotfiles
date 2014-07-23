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


class IsSumDivisionNullAggregate(sql.aggregates.Aggregate):
    is_ordinal = True
    is_computed = False
    # Not used
    sql_function = 'IS_NULL'
    sql_template = 'CASE WHEN SUM(%(divisor)s) IS NULL OR SUM(%(divisor)s) = 0 OR SUM(%(field)s) IS NULL THEN 1 ELSE 0 END'


class IsSumDivisionNull(aggregates.Aggregate):
    name = 'IsSumDivisionNull'

    def __init__(self, col, divisor, **extra):
        super(IsSumDivisionNull, self).__init__(col, divisor=divisor, **extra)

    def add_to_query(self, query, alias, col, source, is_summary):
        query.aggregates[alias] = IsSumDivisionNullAggregate(
            col, source=source, is_summary=is_summary, **self.extra)


class IsSumNullAggregate(sql.aggregates.Aggregate):
    is_ordinal = True
    is_computed = False
    # Not used
    sql_function = 'IS_NULL'
    sql_template = 'CASE WHEN SUM(%(field)s) IS NULL THEN 1 ELSE 0 END'


class IsSumNull(aggregates.Aggregate):
    name = 'IsSumNull'

    def __init__(self, col, **extra):
        super(IsSumNull, self).__init__(col, **extra)

    def add_to_query(self, query, alias, col, source, is_summary):
        query.aggregates[alias] = IsSumNullAggregate(
            col, source=source, is_summary=is_summary, **self.extra)
