import backtosql

from dash import breakdown_helpers


BREAKDOWN = 1
AGGREGATES = 2


class RSBreakdownMixin(object):
    """
    Mixin that defines breakdowns specific model features.
    """

    # TODO rename this
    MISCONCEPTION_DICT = {}

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

    @classmethod
    def translate_dict(cls, dict_):
        """
        Translates dict keys into keys our model understands.
        Returns a copy of the dict.
        """

        if not dict_:
            return dict_

        return {cls.MISCONCEPTION_DICT.get(k, k): v for k, v in dict_.items()}

    @classmethod
    def translate_dicts(cls, list_of_dicts):
        if not list_of_dicts:
            return list_of_dicts

        return [cls.translate_dict(x) for x in list_of_dicts]

    @classmethod
    def translate_breakdown(cls, breakdown):
        """
        Translates breakdown array items into keys our model understands.
        Returns a copy of the dict.
        """

        return [cls.MISCONCEPTION_DICT.get(x, x) for x in breakdown]


class RSContentAdStats(backtosql.Model, RSBreakdownMixin):
    """
    Defines all the fields that are provided by this breakdown model.
    Materialized sub-views are a part of it.
    """

    MISCONCEPTION_DICT = {
        'account': 'account_id',
        'campaign': 'campaign_id',
        'ad_group': 'ad_group_id',
        'content_ad': 'content_ad_id',
        'source': 'source_id',
    }

    date = backtosql.TemplateColumn('part_trunc_date.sql', {'column_name': 'date'}, BREAKDOWN)

    account_id = backtosql.Column('account_id', BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', BREAKDOWN)
    ad_group_id= backtosql.Column('adgroup_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_id = backtosql.Column('source_id', BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, AGGREGATES)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, AGGREGATES)
    cost = backtosql.TemplateColumn('part_sum_cc.sql', {'column_name': 'cost_cc'}, AGGREGATES)
    data_cost = backtosql.TemplateColumn('part_sum_cc.sql', {'column_name': 'data_cost_cc'}, AGGREGATES)

    # BCM
    media_cost = backtosql.TemplateColumn('part_sum_cc.sql', {'column_name': 'cost_cc'}, AGGREGATES)
    e_media_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_cost_nano'}, AGGREGATES)
    e_data_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_data_cost_nano'}, AGGREGATES)
    license_fee = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'license_fee_nano'}, AGGREGATES)
    billing_cost = backtosql.TemplateColumn('part_billing_cost.sql', None, AGGREGATES)
    total_cost = backtosql.TemplateColumn('part_total_cost.sql', None, AGGREGATES)

    # Derivates
    ctr = backtosql.TemplateColumn('part_sumdiv_perc.sql', {'expr': 'clicks', 'divisor': 'impressions'}, AGGREGATES)
    cpc = backtosql.TemplateColumn('part_sumdiv_cc.sql', {'expr': 'cost_cc', 'divisor': 'clicks'}, AGGREGATES)

    # Postclick acquisition fields
    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name':'visits'}, AGGREGATES)
    click_discrepancy = backtosql.TemplateColumn('part_click_discrepancy.sql', None, AGGREGATES)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name':'pageviews'}, AGGREGATES)

    # Postclick engagement fields
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name':'new_visits'}, AGGREGATES)
    percent_new_users = backtosql.TemplateColumn('part_sumdiv_perc.sql', {'expr': 'new_visits', 'divisor': 'visits'}, AGGREGATES)
    bounce_rate = backtosql.TemplateColumn('part_sumdiv_perc.sql', {'expr': 'bounced_visits', 'divisor': 'visits'}, AGGREGATES)
    pv_per_visit = backtosql.TemplateColumn('part_sumdiv.sql', {'expr': 'pageviews', 'divisor':'visits'}, AGGREGATES)
    avg_tos = backtosql.TemplateColumn('part_sumdiv.sql', {'expr': 'total_time_on_site', 'divisor':'visits'}, AGGREGATES)

    @classmethod
    def get_best_view(cls, breakdown):
        # NOTE: best view selection is separated from template preparation
        # as it follows a different kind of logics (does not matter if
        # 'other' row is involved or not, group limits etc.)

        if True:
            return 'contentadstats'

        # TODO the real code for view selection will be like this:
        base = breakdown_helpers.get_base(breakdown)
        structure = breakdown_helpers.get_structure(breakdown)
        delivery = breakdown_helpers.get_delivery(breakdown)
        time = breakdown_helpers.get_time(breakdown)
        l = len(breakdown)

        if base == 'account':
            if l == 1:
                return 'mv_by_acc'

            if structure == 'campaign':
                return 'mv_by_acc_camp' if l == 2 else 'mv_by_acc_camp_ext'
            elif structure == 'source':
                return 'mv_by_acc_sour' if l == 2 else 'mv_by_acc_sour_ext'
            elif structure is None:
                return 'mv_by_acc_ext'
            else:
                raise Exception('Should have all cases covered explicitly')
