import backtosql
from functools import partial

from redshiftapi.constants import ColumnGroup

class RSBreakdownMixin(object):

    @classmethod
    def get_best_view(cls, breakdown, constraints):
        # returns SQL view that best fits the breakdown
        raise NotImplementedError()

    @classmethod
    def get_best_query_template(cls, breakdown, constraints):
        raise NotImplementedError()

    @classmethod
    def get_default_context(cls, breakdown, constraints, order, page):
        # TODO this could be a different API, constraints separately
        # also view might be separate from defautl
        constraints = cls.get_constraints(constraints)
        return {
            'model': cls,
            'view': cls.get_best_view(breakdown, constraints),
            'constraints': constraints,
            'breakdown': cls.select_columns(subset=breakdown),
            'aggregates': cls.select_columns(group=ColumnGroup.AGGREGATES),
            'order': cls.select_order(order),
            'offset': page[0],
            'limit': page[1],
            'params': constraints.get_params() + list(page),
        }


# column definition shortcuts
class AggregateColumn(backtosql.TemplateColumn):
    def __init__(self, column_name, template_name):
        super(AggregateColumn, self).__init__(
            template_name, {'column_name': column_name}, ColumnGroup.AGGREGATES)


class SumDivColumn(backtosql.TemplateColumn):
    def __init__(self, expr, divisor, template_name='part_sumdiv.sql'):
        super(SumDivColumn, self).__init__(
            template_name, {'expr': expr, 'divisor': divisor}, ColumnGroup.AGGREGATES)


SumColumn = partial(AggregateColumn, template_name='part_sum.sql')
SumCCColumn = partial(AggregateColumn, template_name='part_sum_cc.sql')
SumNanoColumn = partial(AggregateColumn, template_name='part_sum_nano.sql')
SumDivCCColumn = partial(SumDivColumn, template_name='part_sumdiv_cc.sql')
SumDivPercColumn = partial(SumDivColumn, template_name='part_sumdiv_perc.sql')