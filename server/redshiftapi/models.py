import backtosql
import copy

import dash.constants
import stats.constants

from redshiftapi import helpers
from redshiftapi import view_selector

BREAKDOWN = 1
AGGREGATE = 2
YESTERDAY_AGGREGATES = 3
CONVERSION_AGGREGATES = 4
TOUCHPOINTS_AGGREGATES = 5
AFTER_JOIN_AGGREGATES = 6


class BreakdownsBase(backtosql.Model):
    date = backtosql.Column('date', BREAKDOWN)

    day = backtosql.Column('date', BREAKDOWN)
    week = backtosql.TemplateColumn('part_trunc_week.sql', {'column_name': 'date'}, BREAKDOWN)
    month = backtosql.TemplateColumn('part_trunc_month.sql', {'column_name': 'date'}, BREAKDOWN)

    agency_id = backtosql.Column('agency_id', BREAKDOWN)
    account_id = backtosql.Column('account_id', BREAKDOWN)
    campaign_id = backtosql.Column('campaign_id', BREAKDOWN)
    ad_group_id = backtosql.Column('ad_group_id', BREAKDOWN)
    content_ad_id = backtosql.Column('content_ad_id', BREAKDOWN)
    source_id = backtosql.Column('source_id', BREAKDOWN)
    publisher = backtosql.Column('publisher', BREAKDOWN)

    @classmethod
    def get_best_view(cls, needed_dimensions, use_publishers_view):
        """ Returns the SQL view that best fits the breakdown """
        raise NotImplementedError()

    def get_breakdown(self, breakdown):
        """ Selects breakdown subset of columns """

        if 'publisher_id' in breakdown:
            publisher_id_idx = breakdown.index('publisher_id')
            breakdown = breakdown[:publisher_id_idx] + ['publisher', 'source_id'] + breakdown[publisher_id_idx + 1:]

        return self.select_columns(subset=breakdown)

    def get_aggregates(self):
        """ Returns all the aggregate columns """
        return self.select_columns(group=AGGREGATE)

    def get_constraints(self, constraints, parents):
        constraints = copy.copy(constraints)

        publisher = constraints.pop('publisher_id', None)
        publisher__neq = constraints.pop('publisher_id__neq', None)

        constraints = backtosql.Q(self, **constraints)

        parent_constraints = self.get_parent_constraints(parents)
        if parent_constraints is not None:
            constraints = constraints & parent_constraints

        if publisher is not None:
            if not publisher:
                # this is the case when we want to query blacklisted publishers but there are no blacklisted publishers
                # modify constraints to not return anything
                constraints = backtosql.Q.none(self)
            else:
                constraints = constraints & self.get_parent_constraints([{'publisher_id': x} for x in publisher])

        if publisher__neq:
            constraints = constraints & ~self.get_parent_constraints([{'publisher_id': x} for x in publisher__neq])

        return constraints

    def get_parent_constraints(self, parents):
        parent_constraints = None

        if parents:
            parents = helpers.inflate_parent_constraints(parents)
            parents = helpers.optimize_parent_constraints(parents)

            parent_constraints = backtosql.Q(self, *[backtosql.Q(self, **x) for x in parents])
            parent_constraints.join_operator = parent_constraints.OR

        return parent_constraints

    def get_query_all_context(self, breakdown, constraints, parents, orders, use_publishers_view):
        return {
            'breakdown': self.get_breakdown(breakdown),
            'aggregates': self.get_aggregates(),
            'constraints': self.get_constraints(constraints, parents),
            'view': self.get_best_view(helpers.get_all_dimensions(
                breakdown, constraints, parents), use_publishers_view),
            'orders': [self.get_column(x).as_order(x, nulls='last') for x in orders],
        }

    def get_query_all_yesterday_context(self, breakdown, constraints, parents, orders, use_publishers_view):
        constraints = helpers.get_yesterday_constraints(constraints)

        yesterday_cost = backtosql.TemplateColumn('part_sum_nano_double.sql',
                                                  {'column_name1': 'cost_nano', 'column_name2': 'data_cost_nano'},
                                                  alias='yesterday_cost')
        e_yesterday_cost = backtosql.TemplateColumn('part_sum_nano_double.sql',
                                                    {'column_name1': 'effective_cost_nano',
                                                        'column_name2': 'effective_data_cost_nano'},
                                                    alias='e_yesterday_cost')

        self.add_column(yesterday_cost)
        self.add_column(e_yesterday_cost)

        return {
            'breakdown': self.get_breakdown(breakdown),
            'aggregates': self.select_columns(['yesterday_cost', 'e_yesterday_cost']),
            'constraints': self.get_constraints(constraints, parents),
            'view': self.get_best_view(helpers.get_all_dimensions(
                breakdown, constraints, parents), use_publishers_view),
            'orders': [self.get_column(x).as_order(x, nulls='last') for x in orders],
        }


class MVMaster(BreakdownsBase):
    device_type = backtosql.Column('device_type', BREAKDOWN)
    country = backtosql.Column('country', BREAKDOWN)
    state = backtosql.Column('state', BREAKDOWN)
    dma = backtosql.Column('dma', BREAKDOWN)
    age = backtosql.Column('age', BREAKDOWN)
    gender = backtosql.Column('gender', BREAKDOWN)
    age_gender = backtosql.Column('age_gender', BREAKDOWN)
    placement_type = backtosql.Column('placement_type', BREAKDOWN)
    video_playback_method = backtosql.Column('video_playback_method', BREAKDOWN)

    clicks = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'clicks'}, AGGREGATE)
    impressions = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'impressions'}, AGGREGATE)
    media_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'cost_nano'}, AGGREGATE)
    data_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'data_cost_nano'}, AGGREGATE)

    # BCM
    e_media_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_cost_nano'}, AGGREGATE)
    e_data_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_data_cost_nano'},
                                           AGGREGATE)
    license_fee = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'license_fee_nano'}, AGGREGATE)
    billing_cost = backtosql.TemplateColumn('part_billing_cost.sql', None, AGGREGATE)
    total_cost = backtosql.TemplateColumn('part_total_cost.sql', None, AGGREGATE)
    margin = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'margin_nano'}, AGGREGATE)
    agency_total = backtosql.TemplateColumn('part_agency_total.sql', None, AGGREGATE)

    # Derivates
    ctr = backtosql.TemplateColumn('part_sumdiv_perc.sql', {'expr': 'clicks', 'divisor': 'impressions'}, AGGREGATE)
    cpc = backtosql.TemplateColumn('part_sumdiv_nano.sql', {'expr': 'cost_nano', 'divisor': 'clicks'}, AGGREGATE)
    cpm = backtosql.TemplateColumn('part_cpm.sql', group=AGGREGATE)

    # Postclick acquisition fields
    visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'visits'}, AGGREGATE)
    click_discrepancy = backtosql.TemplateColumn('part_click_discrepancy.sql', None, AGGREGATE)
    pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, AGGREGATE)

    # Postclick engagement fields
    new_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, AGGREGATE)
    percent_new_users = backtosql.TemplateColumn('part_sumdiv_perc.sql',
                                                 {'expr': 'new_visits', 'divisor': 'visits'}, AGGREGATE)
    bounce_rate = backtosql.TemplateColumn('part_sumdiv_perc.sql',
                                           {'expr': 'bounced_visits', 'divisor': 'visits'}, AGGREGATE)
    pv_per_visit = backtosql.TemplateColumn('part_sumdiv.sql', {'expr': 'pageviews', 'divisor': 'visits'},
                                            AGGREGATE)
    avg_tos = backtosql.TemplateColumn('part_sumdiv.sql',
                                       {'expr': 'total_time_on_site', 'divisor': 'visits'}, AGGREGATE)
    returning_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'returning_users'}, AGGREGATE)
    unique_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'users'}, AGGREGATE)
    new_users = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'new_visits'}, AGGREGATE)
    bounced_visits = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'bounced_visits'}, AGGREGATE)

    total_seconds = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'total_time_on_site'}, AGGREGATE)
    avg_cost_per_minute = backtosql.TemplateColumn('part_avg_cost_per_minute.sql', group=AGGREGATE)
    non_bounced_visits = backtosql.TemplateColumn('part_non_bounced_visits.sql', group=AGGREGATE)
    avg_cost_per_non_bounced_visit = backtosql.TemplateColumn('part_avg_cost_per_non_bounced_visit.sql',
                                                              group=AGGREGATE)
    total_pageviews = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'pageviews'}, group=AGGREGATE)
    avg_cost_per_pageview = backtosql.TemplateColumn('part_sumdiv_nano.sql', {
        'expr': 'cost_nano', 'divisor': 'pageviews',
    }, AGGREGATE)
    avg_cost_for_new_visitor = backtosql.TemplateColumn('part_sumdiv_nano.sql', {
        'expr': 'cost_nano', 'divisor': 'new_visits',
    }, AGGREGATE)
    avg_cost_per_visit = backtosql.TemplateColumn('part_sumdiv_nano.sql', {
        'expr': 'cost_nano', 'divisor': 'visits',
    }, AGGREGATE)

    # Video
    video_start = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'video_start'}, AGGREGATE)
    video_first_quartile = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'video_first_quartile'}, AGGREGATE)
    video_midpoint = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'video_midpoint'}, AGGREGATE)
    video_third_quartile = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'video_third_quartile'}, AGGREGATE)
    video_complete = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'video_complete'}, AGGREGATE)
    video_progress_3s = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'video_progress_3s'}, AGGREGATE)

    # Video  derivates
    video_cpv = backtosql.TemplateColumn('part_sumdiv_nano.sql', {'expr': 'cost_nano', 'divisor': 'video_progress_3s'},
                                         AGGREGATE)
    video_cpcv = backtosql.TemplateColumn('part_sumdiv_nano.sql', {'expr': 'cost_nano', 'divisor': 'video_complete'},
                                          AGGREGATE)

    @classmethod
    def get_best_view(cls, needed_dimensions, use_publishers_view):
        return view_selector.get_best_view_base(needed_dimensions, use_publishers_view)


class MVMasterPublishers(MVMaster):

    publisher_id = backtosql.TemplateColumn('part_publisher_id.sql', None, AGGREGATE)
    external_id = backtosql.TemplateColumn('part_max.sql', {'column_name': 'external_id'}, AGGREGATE)

    def get_query_all_yesterday_context(self, breakdown, constraints, parents, orders, use_publishers_view):
        context = super(MVMasterPublishers, self).get_query_all_yesterday_context(
            breakdown, constraints, parents, orders, use_publishers_view)
        context['aggregates'] += [self.publisher_id]
        return context


class MVTouchpointConversions(BreakdownsBase):
    slug = backtosql.Column('slug', BREAKDOWN)
    window = backtosql.Column('conversion_window', BREAKDOWN)

    count = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'conversion_count'}, AGGREGATE)
    conversion_value = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'conversion_value_nano'}, AGGREGATE)

    @classmethod
    def get_best_view(cls, needed_dimensions, use_publishers_view):
        return view_selector.get_best_view_touchpoints(needed_dimensions, use_publishers_view)


class MVTouchpointConversionsPublishers(MVTouchpointConversions):
    publisher_id = backtosql.TemplateColumn('part_publisher_id.sql', None, AGGREGATE)


class MVConversions(BreakdownsBase):
    slug = backtosql.Column('slug', BREAKDOWN)
    count = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'conversion_count'}, AGGREGATE)

    @classmethod
    def get_best_view(cls, needed_dimensions, use_publishers_view):
        return view_selector.get_best_view_conversions(needed_dimensions, use_publishers_view)


class MVConversionsPublishers(MVConversions):
    publisher_id = backtosql.TemplateColumn('part_publisher_id.sql', None, AGGREGATE)


class MVJointMaster(MVMaster):

    yesterday_cost = backtosql.TemplateColumn('part_sum_nano_double.sql',
                                              {'column_name1': 'cost_nano', 'column_name2': 'data_cost_nano'},
                                              group=YESTERDAY_AGGREGATES)
    e_yesterday_cost = backtosql.TemplateColumn('part_sum_nano_double.sql',
                                                {'column_name1': 'effective_cost_nano',
                                                 'column_name2': 'effective_data_cost_nano'},
                                                group=YESTERDAY_AGGREGATES)

    def init_conversion_columns(self, conversion_goals):
        if not conversion_goals:
            return

        # dynamically generate columns based on conversion goals
        for conversion_goal in conversion_goals:
            if conversion_goal.type not in dash.constants.REPORT_GOAL_TYPES:
                continue

            conversion_key = conversion_goal.get_view_key(conversion_goals)
            column = backtosql.TemplateColumn(
                'part_conversion_goal.sql', {'goal_id': conversion_goal.get_stats_key()},
                alias=conversion_key, group=CONVERSION_AGGREGATES)
            self.add_column(column)

            avg_cost_column = backtosql.TemplateColumn(
                'part_avg_cost_per_conversion_goal.sql', {'conversion_key': conversion_key},
                alias='avg_cost_per_' + conversion_key, group=AFTER_JOIN_AGGREGATES)
            self.add_column(avg_cost_column)

    def init_pixel_columns(self, pixels):
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
                    alias=pixel_key, group=TOUCHPOINTS_AGGREGATES)
                self.add_column(column)

                total_conversion_value_column = backtosql.TemplateColumn(
                    'part_total_conversion_value.sql', {
                        'account_id': pixel.account_id,
                        'slug': pixel.slug,
                        'window': conversion_window,
                    },
                    alias='total_conversion_value_' + pixel_key, group=TOUCHPOINTS_AGGREGATES)
                self.add_column(total_conversion_value_column)

                avg_cost_column = backtosql.TemplateColumn(
                    'part_avg_cost_per_conversion_goal.sql', {'conversion_key': pixel_key},
                    alias='avg_cost_per_' + pixel_key, group=AFTER_JOIN_AGGREGATES)
                self.add_column(avg_cost_column)

                roas_column = backtosql.TemplateColumn(
                    'part_roas.sql', {'conversion_key': pixel_key},
                    alias='roas_' + pixel_key, group=AFTER_JOIN_AGGREGATES)
                self.add_column(roas_column)

    def init_performance_columns(self, campaign_goals, campaign_goal_values, conversion_goals, pixels,
                                 supports_conversions=True):
        if not campaign_goals:
            return

        map_camp_goal_vals = {x.campaign_goal_id: x for x in campaign_goal_values or []}
        map_conversion_goals = {x.id: x for x in conversion_goals or []}
        pixel_ids = [x.id for x in pixels] if pixels else []

        for campaign_goal in campaign_goals:
            conversion_key = None
            metric_column = None

            if campaign_goal.type == dash.constants.CampaignGoalKPI.CPA:
                if not supports_conversions:
                    continue

                if campaign_goal.conversion_goal_id not in map_conversion_goals:
                    # if conversion goal is not amongst campaign goals do not calculate performance
                    continue

                conversion_goal = map_conversion_goals[campaign_goal.conversion_goal_id]

                if conversion_goal.pixel_id not in pixel_ids:
                    # in case pixel is not part of this query (eg archived etc)
                    continue

                conversion_key = conversion_goal.get_view_key(conversion_goals)
                column_group = AFTER_JOIN_AGGREGATES
            else:
                metric_column = dash.campaign_goals.CAMPAIGN_GOAL_PRIMARY_METRIC_MAP[campaign_goal.type]
                column_group = AFTER_JOIN_AGGREGATES

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

    def get_query_joint_context(self, breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view):

        needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
        supports_conversions = view_selector.supports_conversions(needed_dimensions, use_publishers_view)

        # FIXME: temp fix account level publishers view with lots of campaign goals
        skip_performance_columns = 'publisher_id' in breakdown and\
                                   not set(['campaign_id', 'ad_group_id']) & set(constraints.keys())

        if supports_conversions:
            self.init_conversion_columns(goals.conversion_goals)
            self.init_pixel_columns(goals.pixels)

        if not skip_performance_columns:
            self.init_performance_columns(
                goals.campaign_goals, goals.campaign_goal_values, goals.conversion_goals, goals.pixels,
                supports_conversions=supports_conversions)

        order_cols = self.select_columns(orders)
        orders = [x.as_order(orders[i], nulls='last') for i, x in enumerate(order_cols)]

        context = {
            'breakdown': self.get_breakdown(breakdown),
            'partition': self.get_breakdown(stats.constants.get_parent_breakdown(breakdown)),

            'constraints': self.get_constraints(constraints, parents),
            'yesterday_constraints': self.get_constraints(helpers.get_yesterday_constraints(constraints), parents),

            'aggregates': self.get_aggregates(),
            'yesterday_aggregates': self.select_columns(group=YESTERDAY_AGGREGATES),
            'after_join_aggregates': self.select_columns(group=AFTER_JOIN_AGGREGATES),

            'offset': offset,
            'limit': limit,

            'orders': orders,

            'base_view': view_selector.get_best_view_base(needed_dimensions, use_publishers_view),
            'yesterday_view': view_selector.get_best_view_base(needed_dimensions, use_publishers_view),
        }

        if supports_conversions:
            context.update({
                'conversions_constraints': self.get_constraints(constraints, parents),
                'touchpoints_constraints': self.get_constraints(constraints, parents),

                'conversions_aggregates': self.select_columns(group=CONVERSION_AGGREGATES),
                'touchpoints_aggregates': self.select_columns(group=TOUCHPOINTS_AGGREGATES),

                'conversions_view': view_selector.get_best_view_conversions(needed_dimensions, use_publishers_view),
                'touchpoints_view': view_selector.get_best_view_touchpoints(needed_dimensions, use_publishers_view),
            })

        return context


class MVJointMasterPublishers(MVJointMaster):

    publisher_id = backtosql.TemplateColumn('part_publisher_id.sql', None, AGGREGATE)
    external_id = backtosql.TemplateColumn('part_max.sql', {'column_name': 'external_id'}, AGGREGATE)
