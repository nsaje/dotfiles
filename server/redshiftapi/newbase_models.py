import backtosql
import copy

from utils import dates_helper

import dash.constants
from dash import conversions_helper

from stats import constants as sc

from redshiftapi import model_helpers as mh
from redshiftapi import models
from redshiftapi import helpers


class BreakdownsBase(backtosql.Model):
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

    @classmethod
    def get_best_view(cls, needed_dimensions):
        """ Returns the SQL view that best fits the breakdown """
        raise NotImplementedError()

    def get_breakdown(self, breakdown):
        """ Selects breakdown subset of columns """
        if 'publisher_id' in breakdown:
            publisher_id_idx = breakdown.index('publisher_id')
            breakdown = breakdown[:publisher_id_idx] + ['publisher', 'source_id'] + breakdown[publisher_id_idx+1:]

        return self.select_columns(subset=breakdown)

    def get_aggregates(self):
        """ Returns all the aggregate columns """
        return self.select_columns(group=mh.AGGREGATES)

    def get_constraints(self, constraints, parents):
        constraints = copy.copy(constraints)

        publisher = constraints.pop('publisher_id', None)
        publisher__neq = constraints.pop('publisher_id__neq', None)

        constraints = backtosql.Q(self, **constraints)

        if publisher is not None:
            constraints = constraints & self.get_parent_constraints([{'publisher_id': x} for x in publisher])

        if publisher__neq is not None:
            constraints = constraints & ~self.get_parent_constraints([{'publisher_id': x} for x in publisher__neq])

        parent_constraints = self.get_parent_constraints(parents)
        if parent_constraints is not None:
            constraints = constraints & parent_constraints

        return constraints

    def get_parent_constraints(self, parents):
        parent_constraints = None

        if parents:
            parents = helpers.inflate_parent_constraints(parents)
            parents = helpers.optimize_parent_constraints(parents)

            parent_constraints = backtosql.Q(self, *[backtosql.Q(self, **x) for x in parents])
            parent_constraints.join_operator = parent_constraints.OR

        return parent_constraints

    def get_default_context(self, breakdown, constraints, parents, use_publishers_view):
        return {
            'breakdown': self.get_breakdown(breakdown),
            'aggregates': self.get_aggregates(),
            'constraints': self.get_constraints(constraints, parents),
            'view': self.get_best_view(helpers.get_all_dimensions(breakdown, constraints, parents, use_publishers_view)),
            'order': self.get_column(self.DEFAULT_ORDER),
        }

    def supports_all_dimensions(self, needed_dimensions):
        try:
            self.select_columns(subset=needed_dimensions)
        except backtosql.BackToSQLException:
            return False
        return True


class MVMaster(BreakdownsBase):
    DEFAULT_ORDER = '-clicks'

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

    @classmethod
    def get_best_view(cls, needed_dimensions):
        for available, view in models.MATERIALIZED_VIEWS:
            if len(needed_dimensions - available) == 0:
                return view['base']
        return 'mv_master'


class MVMasterPublishers(MVMaster):

    publisher_id = backtosql.TemplateColumn('part_publisher_id.sql', None, mh.AGGREGATES)
    external_id = backtosql.TemplateColumn('part_max.sql', {'column_name': 'external_id'}, mh.AGGREGATES)


class MVMasterYesterday(MVMaster):
    DEFAULT_ORDER = '-yesterday_cost'

    yesterday_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'cost_nano'}, mh.AGGREGATES)
    e_yesterday_cost = backtosql.TemplateColumn('part_sum_nano.sql', {'column_name': 'effective_cost_nano'}, mh.AGGREGATES)

    def get_aggregates(self):
        return self.select_columns(subset=['yesterday_cost', 'e_yesterday_cost'])


class MVTouchpointConversions(BreakdownsBase):
    DEFAULT_ORDER = '-count'

    slug = backtosql.Column('slug', mh.BREAKDOWN)
    window = backtosql.Column('conversion_window', mh.BREAKDOWN)

    count = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'conversion_count'}, mh.AGGREGATES)

    @classmethod
    def get_best_view(cls, needed_dimensions):
        for available, view in models.MATERIALIZED_VIEWS:
            if len(needed_dimensions - available) == 0:
                return view['touchpointconversions']
        return 'mv_touchpointconversions'


class MVConversions(BreakdownsBase):
    DEFAULT_ORDER = '-count'

    slug = backtosql.Column('slug', mh.BREAKDOWN)
    count = backtosql.TemplateColumn('part_sum.sql', {'column_name': 'conversion_count'}, mh.AGGREGATES)

    @classmethod
    def get_best_view(cls, needed_dimensions):
        for available, view in models.MATERIALIZED_VIEWS:
            if len(needed_dimensions - available) == 0:
                return view['conversions']
        return 'mv_conversions'
