import backtosql
import copy

from utils import dates_helper
from dash import conversions_helper

from stats import constants as sc

from redshiftapi import model_helpers as mh


MATERIALIZED_VIEWS = [
    ({
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.SOURCE
    }, {
        'base': 'mv_account',
        'conversions': 'mv_conversions_account',
        'touchpointconversions': 'mv_touch_account',
    }),
    ({
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.SOURCE
    } | set(sc.DeliveryDimension._ALL), {
        'base': 'mv_account_delivery',
    }),
    ({
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.CAMPAIGN
    }, {
        'base': 'mv_campaign',
        'conversions': 'mv_conversions_campaign',
        'touchpointconversions': 'mv_touch_campaign',
    }),
    ({
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.CAMPAIGN
    } | set(sc.DeliveryDimension._ALL), {
        'base': 'mv_campaign_delivery',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP
    }, {
        'base': 'mv_ad_group',
        'conversions': 'mv_conversions_ad_group',
        'touchpointconversions': 'mv_touch_ad_group',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP
    } | set(sc.DeliveryDimension._ALL), {
        'base': 'mv_ad_group_delivery',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP,
        sc.StructureDimension.CONTENT_AD
    }, {
        'base': 'mv_content_ad',
        'conversions': 'mv_conversions_content_ad',
        'touchpointconversions': 'mv_touch_content_ad',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP,
        sc.StructureDimension.CONTENT_AD
    } | set(sc.DeliveryDimension._ALL), {
        'base': 'mv_content_ad_delivery',
    }),
]


class MVMaster(backtosql.Model, mh.RSBreakdownMixin):
    """
    Defines all the fields that are provided by this breakdown model.
    Materialized sub-views are a part of it.
    """

    def __init__(self, conversion_goals=None):
        super(MVMaster, self).__init__()

        self.init_conversion_columns(conversion_goals)

    date = backtosql.Column('date', mh.BREAKDOWN)

    day = backtosql.Column('date', mh.BREAKDOWN)
    week = backtosql.TemplateColumn('part_trunc_week.sql', {'column_name': 'date'}, mh.BREAKDOWN)
    month = backtosql.TemplateColumn('part_trunc_month.sql', {'column_name': 'date'}, mh.BREAKDOWN)

    agency_id = backtosql.Column('agency_id', mh.BREAKDOWN)
    account_id = backtosql.Column('account_id', mh.BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', mh.BREAKDOWN)
    ad_group_id = backtosql.Column('ad_group_id', mh.BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', mh.BREAKDOWN)
    source_id = backtosql.Column('source_id', mh.BREAKDOWN)
    publisher = backtosql.Column('publisher', mh.BREAKDOWN)

    device_type = backtosql.Column('device_type', mh.BREAKDOWN)
    country = backtosql.Column('country', mh.BREAKDOWN)
    state = backtosql.Column('state', mh.BREAKDOWN)
    dma = backtosql.Column('dma', mh.BREAKDOWN)
    age = backtosql.Column('age', mh.BREAKDOWN)
    gender = backtosql.Column('gender', mh.BREAKDOWN)
    age_gender = backtosql.Column('age_gender', mh.BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, mh.AGGREGATES)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, mh.AGGREGATES)
    cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'cost_nano'}, mh.AGGREGATES)
    data_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'data_cost_nano'}, mh.AGGREGATES)

    # BCM
    media_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'cost_nano'}, mh.AGGREGATES)
    e_media_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_cost_nano'}, mh.AGGREGATES)
    e_data_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_data_cost_nano'},
                                           mh.AGGREGATES)
    license_fee = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'license_fee_nano'}, mh.AGGREGATES)
    billing_cost = backtosql.TemplateColumn('part_billing_cost.sql', None, mh.AGGREGATES)
    total_cost = backtosql.TemplateColumn('part_total_cost.sql', None, mh.AGGREGATES)
    margin = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'margin_nano'}, mh.AGGREGATES)
    agency_total = backtosql.TemplateColumn('part_agency_total.sql', None, mh.AGGREGATES)

    # Derivates
    ctr = backtosql.TemplateColumn('part_sumdiv_perc.sql', {'expr': 'clicks', 'divisor': 'impressions'}, mh.AGGREGATES)
    cpc = backtosql.TemplateColumn('part_sumdiv_nano.sql', {'expr': 'cost_nano', 'divisor': 'clicks'}, mh.AGGREGATES)

    # Postclick acquisition fields
    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'visits'}, mh.AGGREGATES)
    click_discrepancy = backtosql.TemplateColumn('part_click_discrepancy.sql', None, mh.AGGREGATES)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, mh.AGGREGATES)

    # Postclick engagement fields
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, mh.AGGREGATES)
    percent_new_users = backtosql.TemplateColumn('part_sumdiv_perc.sql',
                                                 {'expr': 'new_visits', 'divisor': 'visits'}, mh.AGGREGATES)
    bounce_rate = backtosql.TemplateColumn('part_sumdiv_perc.sql',
                                           {'expr': 'bounced_visits', 'divisor': 'visits'}, mh.AGGREGATES)
    pv_per_visit = backtosql.TemplateColumn('part_sumdiv.sql', {'expr': 'pageviews', 'divisor': 'visits'},
                                            mh.AGGREGATES)
    avg_tos = backtosql.TemplateColumn('part_sumdiv.sql',
                                       {'expr': 'total_time_on_site', 'divisor': 'visits'}, mh.AGGREGATES)

    total_seconds = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_time_on_site'}, mh.AGGREGATES)
    avg_cost_per_minute = backtosql.TemplateColumn('part_avg_cost_per_minute.sql', group=mh.AGGREGATES)
    unbounced_visits = backtosql.TemplateColumn('part_unbounced_visits.sql', group=mh.AGGREGATES)
    avg_cost_per_non_bounced_visitor = backtosql.TemplateColumn('part_avg_cost_per_non_bounced_visitor.sql',
                                                                group=mh.AGGREGATES)
    total_pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, group=mh.AGGREGATES)
    avg_cost_per_pageview = backtosql.TemplateColumn('part_sumdiv_nano.sql', {
        'expr': 'cost_nano', 'divisor': 'pageviews',
    }, mh.AGGREGATES)
    avg_cost_for_new_visitor = backtosql.TemplateColumn('part_sumdiv_nano.sql', {
        'expr': 'cost_nano', 'divisor': 'new_visits',
    }, mh.AGGREGATES)
    avg_cost_per_visit = backtosql.TemplateColumn('part_sumdiv_nano.sql', {
        'expr': 'cost_nano', 'divisor': 'visits',
    }, mh.AGGREGATES)

    yesterday_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'cost_nano'},
                                              group=mh.YESTERDAY_COST_AGGREGATES)
    e_yesterday_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_cost_nano'},
                                                group=mh.YESTERDAY_COST_AGGREGATES)

    def init_conversion_columns(self, conversion_goals):
        """
        Conversion columns are added dynamically, because the number and their definition
        depends on the conversion_goals collection.
        """

        if not conversion_goals:
            return

        # dynamically generate columns based on conversion goals
        for conversion_goal in conversion_goals:
            conversion_key = conversion_goal.get_view_key(conversion_goals)

            if conversion_goal.type in conversions_helper.REPORT_GOAL_TYPES:
                column = backtosql.TemplateColumn(
                    'part_conversion_goal.sql', {'goal_id': conversion_goal.get_stats_key()},
                    alias=conversion_key, group=mh.CONVERSION_AGGREGATES
                )

                self.add_column(column)

            elif conversion_goal.type == conversions_helper.PIXEL_GOAL_TYPE:
                goal_id = conversion_goal.pixel.slug if conversion_goal.pixel else conversion_goal.goal_id
                column = backtosql.TemplateColumn(
                    'part_touchpointconversion_goal.sql', {
                        'goal_id': goal_id,
                        'window': conversion_goal.conversion_window,
                    },
                    alias=conversion_key, group=mh.TOUCHPOINTCONVERSION_AGGREGATES
                )
                self.add_column(column)

            avg_cost_column = backtosql.TemplateColumn(
                'part_avg_cost_per_conversion_goal.sql', {'conversion_key': conversion_key},
                alias='avg_cost_per_' + conversion_key, group=mh.AFTER_JOIN_CALCULATIONS
            )

            self.add_column(avg_cost_column)

    @classmethod
    def get_best_view(cls, breakdown, constraints):
        """
        Selects the most suitable materialized view for the selected breakdown.
        """

        base = sc.get_base_dimension(breakdown)
        structure = sc.get_structure_dimension(breakdown)
        delivery = sc.get_delivery_dimension(breakdown)
        level = sc.get_level_dimension(constraints)

        # find first one that matches
        breakdown = set(x for x in (base, structure, delivery, level) if x)

        for available, view in MATERIALIZED_VIEWS:
            if len(breakdown - available) == 0:
                return view

        if delivery:
            return {
                'base': 'mv_master',
            }

        return {
            'base': 'mv_master',
            'conversions': 'mv_conversions',
            'touchpointconversions': 'mv_touchpointconversions',
        }

    def get_default_context(self, breakdown, constraints, breakdown_constraints,
                            order, offset, limit):
        """
        Returns the template context that is used by most of templates
        """

        breakdown_constraints_q = None
        if breakdown_constraints:
            breakdown_constraints_q = backtosql.Q(self, *[backtosql.Q(self, **x) for x in breakdown_constraints])
            breakdown_constraints_q.join_operator = breakdown_constraints_q.OR

        breakdown_supports_conversions = self.breakdown_supports_conversions(breakdown)

        order_column = self.get_column(order).as_order(order, nulls='last')

        is_ordered_by_conversions = order_column.group == mh.CONVERSION_AGGREGATES
        is_ordered_by_touchpointconversions = order_column.group == mh.TOUCHPOINTCONVERSION_AGGREGATES
        is_ordered_by_after_join_conversions_calculations = order_column.group == mh.AFTER_JOIN_CALCULATIONS

        # dont order by conversions if breakdown does not support them
        if (not breakdown_supports_conversions and
            (is_ordered_by_touchpointconversions or
             is_ordered_by_conversions or
             is_ordered_by_after_join_conversions_calculations)):
            order_column = self.get_column('clicks').as_order(order, nulls='last')

        context = {
            'view': self.get_best_view(breakdown, constraints),
            'breakdown': self.get_breakdown(breakdown),

            # partition is 1 less than breakdown long - the last dimension is the targeted one
            'breakdown_partition': self.get_breakdown(breakdown)[:-1],

            'constraints': backtosql.Q(self, **constraints),
            'breakdown_constraints': breakdown_constraints_q,
            'aggregates': self.get_aggregates(),
            'order': order_column,
            'offset': offset,
            'limit': limit,

            'is_ordered_by_conversions': (breakdown_supports_conversions and is_ordered_by_conversions),
            'is_ordered_by_touchpointconversions': (breakdown_supports_conversions and
                                                    is_ordered_by_touchpointconversions),
            'conversions_aggregates': (self.select_columns(group=mh.CONVERSION_AGGREGATES)
                                       if breakdown_supports_conversions else []),
            'touchpointconversions_aggregates': (self.select_columns(group=mh.TOUCHPOINTCONVERSION_AGGREGATES)
                                                 if breakdown_supports_conversions else []),

            'after_join_conversions_calculations': (self.select_columns(group=mh.AFTER_JOIN_CALCULATIONS)
                                                    if breakdown_supports_conversions else []),
            'is_ordered_by_after_join_conversions_calculations': (is_ordered_by_after_join_conversions_calculations and
                                                                  breakdown_supports_conversions),
        }

        context.update(get_default_yesterday_context(self, constraints, order_column))

        return context

    def breakdown_supports_conversions(self, breakdown):
        conversion_columns = self.select_columns(group=mh.CONVERSION_AGGREGATES)
        tpconversion_columns = self.select_columns(group=mh.TOUCHPOINTCONVERSION_AGGREGATES)

        return ((conversion_columns or tpconversion_columns) and
                sc.get_delivery_dimension(breakdown) is None)


def get_default_yesterday_context(model, constraints, order_column):
    date_from, date_to = constraints['date__gte'], constraints['date__lte']

    yesterday = dates_helper.local_yesterday()

    if date_from <= yesterday <= date_to:
        # columns that fetch yesterday spend from the base table
        yesterday_cost = backtosql.TemplateColumn(
            'part_for_date_sum_nano.sql',
            {
                'column_name': 'cost_nano',
                'date_column_name': 'date',
                'date': yesterday.isoformat(),
            },
            alias='yesterday_cost',
            group=mh.YESTERDAY_COST_AGGREGATES)
        e_yesterday_cost = backtosql.TemplateColumn(
            'part_for_date_sum_nano.sql',
            {
                'column_name': 'effective_cost_nano',
                'date_column_name': 'date',
                'date': yesterday.isoformat(),
            },
            alias='e_yesterday_cost',
            group=mh.YESTERDAY_COST_AGGREGATES)

        context = {
            'yesterday_aggregates': [yesterday_cost, e_yesterday_cost]
        }
    else:
        # columns that fetch yesterday spend in a special select statement that
        # is then joined to the base select

        constraints = copy.copy(constraints)

        # replace date range with yesterday date
        constraints.pop('date__gte', None)
        constraints.pop('date__lte', None)
        constraints['date'] = dates_helper.local_yesterday()

        context = {
            'yesterday_constraints': backtosql.Q(model, **constraints),
            'yesterday_aggregates': model.select_columns(group=mh.YESTERDAY_COST_AGGREGATES),
        }

    context['is_ordered_by_yesterday_aggregates'] = order_column.group == mh.YESTERDAY_COST_AGGREGATES

    return context
