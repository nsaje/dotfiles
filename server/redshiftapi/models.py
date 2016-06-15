import backtosql

from stats import constants

from redshiftapi.model_helpers import RSBreakdownMixin, AGGREGATES, BREAKDOWN


class MVMaster(backtosql.Model, RSBreakdownMixin):
    """
    Defines all the fields that are provided by this breakdown model.
    Materialized sub-views are a part of it.
    """

    date = backtosql.TemplateColumn('part_trunc_date.sql', {'column_name': 'date'}, BREAKDOWN)

    day = backtosql.TemplateColumn('part_trunc_date.sql', {'column_name': 'date'}, BREAKDOWN)
    week = backtosql.TemplateColumn('part_trunc_week.sql', {'column_name': 'date'}, BREAKDOWN)
    month = backtosql.TemplateColumn('part_trunc_month.sql', {'column_name': 'date'}, BREAKDOWN)

    agency_id = backtosql.Column('agency_id', BREAKDOWN)
    account_id = backtosql.Column('account_id', BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', BREAKDOWN)
    ad_group_id = backtosql.Column('adgroup_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_id = backtosql.Column('source_id', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)

    device_type = backtosql.Column('device_type', BREAKDOWN)
    country = backtosql.Column('country', BREAKDOWN)
    state = backtosql.Column('state', BREAKDOWN)
    dma = backtosql.Column('dma', BREAKDOWN)
    age = backtosql.Column('age', BREAKDOWN)
    gender = backtosql.Column('gender', BREAKDOWN)
    age_gender = backtosql.Column('age_gender', BREAKDOWN)

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
    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'visits'}, AGGREGATES)
    click_discrepancy = backtosql.TemplateColumn('part_click_discrepancy.sql', None, AGGREGATES)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, AGGREGATES)

    # Postclick engagement fields
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, AGGREGATES)
    percent_new_users = backtosql.TemplateColumn('part_sumdiv_perc.sql',
                                                 {'expr': 'new_visits', 'divisor': 'visits'}, AGGREGATES)
    bounce_rate = backtosql.TemplateColumn('part_sumdiv_perc.sql',
                                           {'expr': 'bounced_visits', 'divisor': 'visits'}, AGGREGATES)
    pv_per_visit = backtosql.TemplateColumn('part_sumdiv.sql', {'expr': 'pageviews', 'divisor': 'visits'}, AGGREGATES)
    avg_tos = backtosql.TemplateColumn('part_sumdiv.sql',
                                       {'expr': 'total_time_on_site', 'divisor': 'visits'}, AGGREGATES)

    @classmethod
    def get_best_view(cls, breakdown):
        """
        Selects the most suitable materialized view for the selected breakdown.
        """

        base = constants.get_base_dimension(breakdown)
        structure = constants.get_structure_dimension(breakdown)
        delivery = constants.get_delivery_dimension(breakdown)

        if base == 'account_id' and structure != 'publisher':
            if delivery:
                return 'mv_account_delivery'
            return 'mv_account'

        return 'mv_master'

    @classmethod
    def get_default_context(cls, breakdown, constraints, breakdown_constraints,
                            order, offset, limit):
        """
        Returns the template context that is used by most of templates
        """

        breakdown_constraints_q = None
        if breakdown_constraints:
            breakdown_constraints_q = backtosql.Q(cls, *[backtosql.Q(cls, **x) for x in breakdown_constraints])
            breakdown_constraints_q.join_operator = breakdown_constraints_q.OR

        context = {
            'view': cls.get_best_view(breakdown),
            'breakdown': cls.get_breakdown(breakdown),
            'constraints': backtosql.Q(cls, **constraints),
            'breakdown_constraints': breakdown_constraints_q,
            'aggregates': cls.get_aggregates(),
            'order': cls.select_order([order]),
            'offset': offset,
            'limit': limit,
        }

        return context
