from django.db.models import FloatField
from django.db.models import aggregates


class SumDivision(aggregates.Aggregate):
    function = "SUM_DIVISION"
    template = (
        "CASE WHEN SUM(%(divisor)s) <> 0 THEN SUM(CAST(%(expressions)s AS FLOAT)) / SUM(%(divisor)s) ELSE NULL END"
    )

    def __init__(self, field, divisor, **extra):
        super(SumDivision, self).__init__(field, divisor=divisor, output_field=FloatField(), **extra)


class IsSumDivisionNull(aggregates.Aggregate):
    function = "IS_NULL"
    template = (
        "CASE WHEN SUM(%(divisor)s) IS NULL OR SUM(%(divisor)s) = 0 OR SUM(%(expressions)s) IS NULL THEN 1 ELSE 0 END"
    )

    def __init__(self, col, divisor, **extra):
        super(IsSumDivisionNull, self).__init__(col, divisor=divisor, **extra)


class IsSumNull(aggregates.Aggregate):
    function = "IS_NULL"
    template = "CASE WHEN SUM(%(expressions)s) IS NULL THEN 1 ELSE 0 END"

    def __init__(self, col, **extra):
        super(IsSumNull, self).__init__(col, **extra)


class SumJSONLength(aggregates.Aggregate):
    template = "SUM(JSONB_ARRAY_LENGTH(%(expressions)s))"
