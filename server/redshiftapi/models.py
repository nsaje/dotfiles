import backtosql
import copy

from utils import dates_helper

import dash.constants
from dash import conversions_helper

from stats import constants as sc

from redshiftapi import model_helpers as mh
from redshiftapi import helpers


DeliveryGeo = set([
    sc.DeliveryDimension.COUNTRY,
    sc.DeliveryDimension.STATE,
    sc.DeliveryDimension.DMA,
])


DeliveryDemo = set([
    sc.DeliveryDimension.DEVICE,
    sc.DeliveryDimension.AGE,
    sc.DeliveryDimension.GENDER,
    sc.DeliveryDimension.AGE_GENDER,
])

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
    } | DeliveryGeo, {
        'base': 'mv_account_delivery_geo',
    }),
    ({
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.SOURCE
    } | DeliveryDemo, {
        'base': 'mv_account_delivery_demo',
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
    } | DeliveryGeo, {
        'base': 'mv_campaign_delivery_geo',
    }),
    ({
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.CAMPAIGN
    } | DeliveryDemo, {
        'base': 'mv_campaign_delivery_demo',
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
    } | DeliveryGeo, {
        'base': 'mv_ad_group_delivery_geo',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP
    } | DeliveryDemo, {
        'base': 'mv_ad_group_delivery_demo',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP,
        sc.StructureDimension.PUBLISHER,
    }, {
        'base': 'mv_pubs_ad_group',
        'conversions': 'mv_conversions',
        'touchpointconversions': 'mv_touchpointconversions',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP,
        sc.StructureDimension.PUBLISHER,
    } | DeliveryGeo | DeliveryDemo, {
        'base': 'mv_pubs_master',
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
    } | DeliveryGeo, {
        'base': 'mv_content_ad_delivery_geo',
    }),
    ({
        sc.StructureDimension.SOURCE,
        sc.StructureDimension.ACCOUNT,
        sc.StructureDimension.CAMPAIGN,
        sc.StructureDimension.AD_GROUP,
        sc.StructureDimension.CONTENT_AD
    } | DeliveryDemo, {
        'base': 'mv_content_ad_delivery_demo',
    }),
]


class MVMaster(backtosql.Model, mh.RSBreakdownMixin):
    """
    Defines all the fields that are provided by this breakdown model.
    Materialized sub-views are a part of it.
    """

    def __init__(self, conversion_goals=None, pixels=None, campaign_goals=None, campaign_goal_values=None):
        super(MVMaster, self).__init__()

        self.init_conversion_columns(conversion_goals)
        self.init_campaign_goal_performance_columns(
            campaign_goals, campaign_goal_values, conversion_goals, pixels)
        self.init_pixels(pixels)

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

    external_id = backtosql.TemplateColumn('part_max.sql', {'column_name': 'external_id'}, mh.PUBLISHER_AGGREGATES)
    publisher_id = backtosql.TemplateColumn('part_publisher_id.sql', None, mh.PUBLISHER_AGGREGATES)

    device_type = backtosql.Column('device_type', mh.BREAKDOWN)
    country = backtosql.Column('country', mh.BREAKDOWN)
    state = backtosql.Column('state', mh.BREAKDOWN)
    dma = backtosql.Column('dma', mh.BREAKDOWN)
    age = backtosql.Column('age', mh.BREAKDOWN)
    gender = backtosql.Column('gender', mh.BREAKDOWN)
    age_gender = backtosql.Column('age_gender', mh.BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, mh.AGGREGATES)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, mh.AGGREGATES)
    media_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'cost_nano'}, mh.AGGREGATES)
    data_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'data_cost_nano'}, mh.AGGREGATES)

    # BCM
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
    cpm = backtosql.TemplateColumn('part_cpm.sql', group=mh.AGGREGATES)

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
    returning_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'returning_users'}, mh.AGGREGATES)
    unique_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'users'}, mh.AGGREGATES)
    new_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, mh.AGGREGATES)
    bounced_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bounced_visits'}, mh.AGGREGATES)

    total_seconds = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_time_on_site'}, mh.AGGREGATES)
    avg_cost_per_minute = backtosql.TemplateColumn('part_avg_cost_per_minute.sql', group=mh.AGGREGATES)
    non_bounced_visits = backtosql.TemplateColumn('part_non_bounced_visits.sql', group=mh.AGGREGATES)
    avg_cost_per_non_bounced_visit = backtosql.TemplateColumn('part_avg_cost_per_non_bounced_visit.sql',
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
            if conversion_goal.type not in conversions_helper.REPORT_GOAL_TYPES:
                continue

            conversion_key = conversion_goal.get_view_key(conversion_goals)
            column = backtosql.TemplateColumn(
                'part_conversion_goal.sql', {'goal_id': conversion_goal.get_stats_key()},
                alias=conversion_key, group=mh.CONVERSION_AGGREGATES
            )

            self.add_column(column)

            avg_cost_column = backtosql.TemplateColumn(
                'part_avg_cost_per_conversion_goal.sql', {'conversion_key': conversion_key},
                alias='avg_cost_per_' + conversion_key, group=mh.AFTER_JOIN_CONVERSIONS_CALCULATIONS
            )

            self.add_column(avg_cost_column)

    def init_campaign_goal_performance_columns(self, campaign_goals, campaign_goal_values, conversion_goals, pixels):
        map_camp_goal_vals = {x.campaign_goal_id: x for x in campaign_goal_values or []}
        map_conversion_goals = {x.id: x for x in conversion_goals or []}
        pixel_ids = [x.id for x in pixels] if pixels else []

        if not campaign_goals:
            return

        for campaign_goal in campaign_goals:
            conversion_key = None
            metric_column = None

            if campaign_goal.type == dash.constants.CampaignGoalKPI.CPA:
                if campaign_goal.conversion_goal_id not in map_conversion_goals:
                    # if conversion goal is not amongst campaign goals do not calculate performance
                    continue

                conversion_goal = map_conversion_goals[campaign_goal.conversion_goal_id]

                if conversion_goal.pixel_id not in pixel_ids:
                    # in case pixel is not part of this query (eg archived etc)
                    continue

                conversion_key = conversion_goal.get_view_key(conversion_goals)
                column_group = mh.AFTER_JOIN_CONVERSIONS_CALCULATIONS
            else:
                metric_column = dash.campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP[campaign_goal.type]
                column_group = mh.AFTER_JOIN_CALCULATIONS

            is_cost_dependent = campaign_goal.type in dash.campaign_goals.COST_DEPENDANT_GOALS
            is_inverse_performance = campaign_goal.type in dash.campaign_goals.INVERSE_PERFORMANCE_CAMPAIGN_GOALS

            campaign_goal_value = map_camp_goal_vals.get(campaign_goal.pk)
            if campaign_goal_value and campaign_goal_value.value:
                planned_value = campaign_goal_value.value
            else:
                planned_value = 'NULL'

            column = backtosql.TemplateColumn('part_performance.sql', {
                'is_cost_dependent': is_cost_dependent,
                'is_inverse_performance': is_inverse_performance,
                'has_conversion_key': conversion_key is not None,
                'conversion_key': conversion_key or '0',
                'planned_value':  planned_value,
                'metric_column': metric_column or '-1',
            }, alias='performance_' + campaign_goal.get_view_key(), group=column_group)
            self.add_column(column)

    def init_pixels(self, pixels):
        """
        Pixel columns are added dynamically like conversions, because the number and their definition
        depends on the pixels collection.
        """
        if not pixels:
            return

        conversion_windows = sorted(dash.constants.ConversionWindows.get_all())
        for pixel in pixels:
            for conversion_window in conversion_windows:
                pixel_key = pixel.get_view_key(conversion_window)
                column = backtosql.TemplateColumn(
                    'part_touchpointconversion_goal.sql', {
                        'account_id': pixel.account_id,
                        'slug': pixel.slug,
                        'window': conversion_window,
                    },
                    alias=pixel_key, group=mh.TOUCHPOINTCONVERSION_AGGREGATES
                )
                self.add_column(column)

                avg_cost_column = backtosql.TemplateColumn(
                    'part_avg_cost_per_conversion_goal.sql', {'conversion_key': pixel_key},
                    alias='avg_cost_per_' + pixel_key, group=mh.AFTER_JOIN_CONVERSIONS_CALCULATIONS
                )

                self.add_column(avg_cost_column)

    @classmethod
    def get_best_view(cls, breakdown, constraints, use_publishers_view=False):
        """
        Selects the most suitable materialized view for the selected breakdown.
        """

        constraints_dimensions = [backtosql.dissect_constraint_key(x)[0] for x in constraints.keys()]

        non_date_dimensions = set(sc.StructureDimension._ALL) | set(sc.DeliveryDimension._ALL)
        needed_dimensions = set(constraints_dimensions + breakdown) & non_date_dimensions

        if use_publishers_view:
            needed_dimensions.add('publisher_id')

        for available, view in MATERIALIZED_VIEWS:
            if len(needed_dimensions - available) == 0:
                return view

        if sc.get_delivery_dimension(needed_dimensions):
            return {
                'base': 'mv_master',
            }

        return {
            'base': 'mv_master',
            'conversions': 'mv_conversions',
            'touchpointconversions': 'mv_touchpointconversions',
        }

    def get_default_context(self, breakdown, constraints, parents,
                            order=None, offset=None, limit=None, use_publishers_view=False):
        """
        Returns the template context that is used by most of templates
        """

        breakdown_supports_conversions = self.breakdown_supports_conversions(breakdown)

        if order:
            order_column = self.get_column(order).as_order(order, nulls='last')

            is_ordered_by_conversions = order_column.group == mh.CONVERSION_AGGREGATES
            is_ordered_by_touchpointconversions = order_column.group == mh.TOUCHPOINTCONVERSION_AGGREGATES

            # dont order by conversions if breakdown does not support them
            if (not breakdown_supports_conversions and
                (is_ordered_by_touchpointconversions or
                 is_ordered_by_conversions)):
                order_column = self.get_column('clicks').as_order(order, nulls='last')

            is_ordered_by_after_join_calculations = order_column.group in (
                mh.AFTER_JOIN_CALCULATIONS, mh.AFTER_JOIN_CONVERSIONS_CALCULATIONS)
        else:
            order_column = None
            is_ordered_by_conversions = False
            is_ordered_by_touchpointconversions = False
            is_ordered_by_after_join_calculations = False

        after_join_calculations = self.select_columns(group=mh.AFTER_JOIN_CALCULATIONS)
        if breakdown_supports_conversions:
            after_join_calculations.extend(self.select_columns(group=mh.AFTER_JOIN_CONVERSIONS_CALCULATIONS))

        context = {
            'view': self.get_best_view(breakdown, constraints, use_publishers_view),
            'breakdown': self.get_breakdown(breakdown),

            # partition is 1 less than breakdown long - the last dimension is the targeted one
            'breakdown_partition': self.get_breakdown(sc.get_parent_breakdown(breakdown)),

            'constraints': self.get_constraints(constraints),
            'parent_constraints': self.get_parent_constraints(parents),
            'aggregates': self.get_aggregates(breakdown),
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

            'after_join_calculations': after_join_calculations,
            'is_ordered_by_after_join_calculations': is_ordered_by_after_join_calculations,
        }

        context.update(self.get_default_yesterday_context(constraints, order_column))

        return context

    def breakdown_supports_conversions(self, breakdown):
        conversion_columns = self.select_columns(group=mh.CONVERSION_AGGREGATES)
        tpconversion_columns = self.select_columns(group=mh.TOUCHPOINTCONVERSION_AGGREGATES)

        return ((conversion_columns or tpconversion_columns) and
                sc.get_delivery_dimension(breakdown) is None)

    def get_default_yesterday_context(self, constraints, order_column):
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
                'yesterday_constraints': self.get_constraints(constraints),
                'yesterday_aggregates': self.select_columns(group=mh.YESTERDAY_COST_AGGREGATES),
            }

        if order_column:
            context['is_ordered_by_yesterday_aggregates'] = order_column.group == mh.YESTERDAY_COST_AGGREGATES
        else:
            context['is_ordered_by_yesterday_aggregates'] = False

        return context

    def get_constraints(self, constraints):
        constraints = copy.copy(constraints)

        publisher = constraints.pop('publisher_id', None)
        publisher__neq = constraints.pop('publisher_id__neq', None)

        constraints = backtosql.Q(self, **constraints)

        if publisher is not None:
            constraints = constraints & self.get_parent_constraints([{'publisher_id': x} for x in publisher])

        if publisher__neq is not None:
            constraints = constraints & ~self.get_parent_constraints([{'publisher_id': x} for x in publisher__neq])

        return constraints

    def get_aggregates(self, breakdown):
        aggregates = super(MVMaster, self).get_aggregates()
        if 'publisher_id' in breakdown:
            aggregates = self.select_columns(group=mh.PUBLISHER_AGGREGATES) + aggregates
        return aggregates

    def get_parent_constraints(self, parents):
        parent_constraints = None

        if parents:
            parents = helpers.inflate_parent_constraints(parents)
            parents = helpers.optimize_parent_constraints(parents)

            parent_constraints = backtosql.Q(self, *[backtosql.Q(self, **x) for x in parents])
            parent_constraints.join_operator = parent_constraints.OR

        return parent_constraints

    def get_breakdown(self, breakdown):
        if 'publisher_id' in breakdown:
            publisher_id_idx = breakdown.index('publisher_id')
            breakdown = breakdown[:publisher_id_idx] + ['publisher', 'source_id'] + breakdown[publisher_id_idx+1:]

        return super(MVMaster, self).get_breakdown(breakdown)
