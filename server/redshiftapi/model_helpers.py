
BREAKDOWN = 1
AGGREGATES = 2


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
