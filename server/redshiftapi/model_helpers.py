
BREAKDOWN = 1
AGGREGATES = 2
CONVERSION_AGGREGATES = 3
TOUCHPOINTCONVERSION_AGGREGATES = 4
AFTER_JOIN_CALCULATIONS = 5
YESTERDAY_COST_AGGREGATES = 6
AFTER_JOIN_CONVERSIONS_CALCULATIONS = 7


class RSBreakdownMixin(object):
    """
    Mixin that defines breakdowns specific model features.
    """

    @classmethod
    def get_best_view(cls, breakdown):
        """ Returns the SQL view that best fits the breakdown """
        raise NotImplementedError()

    def get_breakdown(self, breakdown):
        """ Selects breakdown subset of columns """
        return self.select_columns(subset=breakdown)

    def get_aggregates(self):
        """ Returns all the aggregate columns """
        return self.select_columns(group=AGGREGATES)
