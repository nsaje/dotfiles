
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

    @classmethod
    def get_breakdown(cls, breakdown):
        """ Selects breakdown subset of columns """
        return cls.select_columns(subset=breakdown)

    @classmethod
    def get_aggregates(cls):
        """ Returns all the aggregate columns """
        return cls.select_columns(group=AGGREGATES)
