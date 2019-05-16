import collections
import copy

import backtosql
import dash.constants
import stats.constants
from redshiftapi import helpers
from redshiftapi import view_selector
from utils import cache_helper
from utils import converters
from utils.dict_helper import dict_join

BREAKDOWN = 1
AGGREGATE = 2
YESTERDAY_AGGREGATES = 3
CONVERSION_AGGREGATES = 4
TOUCHPOINTS_AGGREGATES = 5
AFTER_JOIN_AGGREGATES = 6

MAX_IDENTIFIER_LENGTH = 63

A_COST_COLUMNS = {"column_name": "cost_nano"}
AT_COST_COLUMNS = {"column_name1": "cost_nano", "column_name2": "data_cost_nano"}
ATFM_COST_COLUMNS = {
    "column_name1": "cost_nano",
    "column_name2": "data_cost_nano",
    "column_name3": "license_fee_nano",
    "column_name4": "margin_nano",
}
ET_COST_COLUMNS = {"column_name1": "effective_cost_nano", "column_name2": "effective_data_cost_nano"}
ETF_COST_COLUMNS = {
    "column_name1": "effective_cost_nano",
    "column_name2": "effective_data_cost_nano",
    "column_name3": "license_fee_nano",
}
ETFM_COST_COLUMNS = {
    "column_name1": "effective_cost_nano",
    "column_name2": "effective_data_cost_nano",
    "column_name3": "license_fee_nano",
    "column_name4": "margin_nano",
}

LOCAL_A_COST_COLUMNS = {"column_name": "local_cost_nano"}
LOCAL_AT_COST_COLUMNS = {"column_name1": "local_cost_nano", "column_name2": "local_data_cost_nano"}
LOCAL_ATFM_COST_COLUMNS = {
    "column_name1": "local_cost_nano",
    "column_name2": "local_data_cost_nano",
    "column_name3": "local_license_fee_nano",
    "column_name4": "local_margin_nano",
}
LOCAL_ET_COST_COLUMNS = {"column_name1": "local_effective_cost_nano", "column_name2": "local_effective_data_cost_nano"}
LOCAL_ETF_COST_COLUMNS = {
    "column_name1": "local_effective_cost_nano",
    "column_name2": "local_effective_data_cost_nano",
    "column_name3": "local_license_fee_nano",
}
LOCAL_ETFM_COST_COLUMNS = {
    "column_name1": "local_effective_cost_nano",
    "column_name2": "local_effective_data_cost_nano",
    "column_name3": "local_license_fee_nano",
    "column_name4": "local_margin_nano",
}


class BreakdownsBase(backtosql.Model):
    date = backtosql.Column("date", BREAKDOWN)

    day = backtosql.Column("date", BREAKDOWN)
    week = backtosql.TemplateColumn("part_trunc_week.sql", {"column_name": "date"}, BREAKDOWN)
    month = backtosql.TemplateColumn("part_trunc_month.sql", {"column_name": "date"}, BREAKDOWN)

    agency_id = backtosql.Column("agency_id", BREAKDOWN)
    account_id = backtosql.Column("account_id", BREAKDOWN)
    campaign_id = backtosql.Column("campaign_id", BREAKDOWN)
    ad_group_id = backtosql.Column("ad_group_id", BREAKDOWN)
    content_ad_id = backtosql.Column("content_ad_id", BREAKDOWN)
    source_id = backtosql.Column("source_id", BREAKDOWN)
    publisher = backtosql.Column("publisher", BREAKDOWN)

    publisher_id = backtosql.TemplateColumn("part_publisher_id.sql")
    external_id = backtosql.TemplateColumn("part_max.sql", {"column_name": "external_id"})

    def get_breakdown(self, breakdown):
        """ Selects breakdown subset of columns """

        if "publisher_id" in breakdown:
            publisher_id_idx = breakdown.index("publisher_id")
            breakdown = breakdown[:publisher_id_idx] + ["publisher", "source_id"] + breakdown[publisher_id_idx + 1 :]

        # remove duplicated dimensions
        breakdown = list(collections.OrderedDict(list(zip(breakdown, breakdown))).keys())

        return self.select_columns(subset=breakdown)

    def get_order(self, order_list):
        return [self.get_column(x).as_order(x, nulls="last") for x in order_list]

    def get_aggregates(self, breakdown, view):
        """ Returns all the aggregate columns """
        columns = self.select_columns(group=AGGREGATE)

        if "publisher_id" in breakdown:
            columns.append(self.publisher_id)

            if view_selector.supports_external_id(view):
                columns.append(self.external_id)

        return columns

    def get_constraints(self, constraints, parents):
        constraints = copy.copy(constraints)

        publisher = constraints.pop("publisher_id", None)
        publisher__neq = constraints.pop("publisher_id__neq", None)

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
                constraints = constraints & self.get_parent_constraints([{"publisher_id": x} for x in publisher])

        if publisher__neq:
            constraints = constraints & ~self.get_parent_constraints([{"publisher_id": x} for x in publisher__neq])

        return constraints

    def get_parent_constraints(self, parents):
        parent_constraints = None

        if parents:
            parents = helpers.inflate_parent_constraints(parents)
            parents = helpers.optimize_parent_constraints(parents)

            parent_constraints = backtosql.Q(self, *[backtosql.Q(self, **x) for x in parents])
            parent_constraints.join_operator = parent_constraints.OR

        return parent_constraints

    def get_query_all_context(self, breakdown, constraints, parents, orders, view):
        constraints, temp_tables = self._constraints_to_temp_tables(constraints)
        return {
            "breakdown": self.get_breakdown(breakdown),
            "aggregates": self.get_aggregates(breakdown, view),
            "constraints": self.get_constraints(constraints, parents),
            "temp_tables": temp_tables,
            "view": view,
            "orders": self.get_order(orders),
        }

    @staticmethod
    def _constraints_to_temp_tables(constraints):
        constraints = copy.copy(constraints)
        temp_tables = set()
        for constraint, value in list(constraints.items()):
            is_collection = isinstance(value, collections.Iterable) and type(value) not in (str, str)
            if not value or not is_collection or not isinstance(value[0], int):
                continue
            table_name = "tmp_filter_{}_{}".format(constraint, cache_helper.get_cache_key(value))[
                :MAX_IDENTIFIER_LENGTH
            ]
            temp_table = backtosql.ConstraintTempTable(table_name, constraint, value)
            constraints[constraint] = temp_table
            temp_tables.add(temp_table)
        return constraints, temp_tables

    def get_query_all_yesterday_context(self, breakdown, constraints, parents, orders, view):
        constraints = helpers.get_yesterday_constraints(constraints)
        constraints, temp_tables = self._constraints_to_temp_tables(constraints)

        aggregates = [
            "yesterday_at_cost",
            "local_yesterday_at_cost",
            "yesterday_et_cost",
            "local_yesterday_et_cost",
            "yesterday_etfm_cost",
            "local_yesterday_etfm_cost",
            "yesterday_cost",
            "local_yesterday_cost",
            "e_yesterday_cost",
            "local_e_yesterday_cost",
        ]
        self.add_column(backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, alias="yesterday_at_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, alias="local_yesterday_at_cost")
        )  # noqa
        self.add_column(backtosql.TemplateColumn("part_2sum_nano.sql", ET_COST_COLUMNS, alias="yesterday_et_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_ET_COST_COLUMNS, alias="local_yesterday_et_cost")
        )  # noqa
        self.add_column(backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, alias="yesterday_etfm_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, alias="local_yesterday_etfm_cost")
        )  # noqa

        # FIXME: Remove the following 4 columns after new margins are completely migrated to
        self.add_column(backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, alias="yesterday_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, alias="local_yesterday_cost")
        )  # noqa
        self.add_column(backtosql.TemplateColumn("part_2sum_nano.sql", ET_COST_COLUMNS, alias="e_yesterday_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_ET_COST_COLUMNS, alias="local_e_yesterday_cost")
        )  # noqa

        if "publisher_id" in breakdown:
            aggregates.append("publisher_id")

        return {
            "breakdown": self.get_breakdown(breakdown),
            "aggregates": self.select_columns(aggregates),
            "constraints": self.get_constraints(constraints, parents),
            "temp_tables": temp_tables,
            "view": view,
            "orders": self.get_order(orders),
        }


class MVMaster(BreakdownsBase):
    # Breakdowns
    device_type = backtosql.Column("device_type", BREAKDOWN, null=True)
    device_os = backtosql.Column("device_os", BREAKDOWN, null=True)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN, null=True)
    placement_medium = backtosql.Column("placement_medium", BREAKDOWN, null=True)

    placement_type = backtosql.Column("placement_type", BREAKDOWN, null=True)
    video_playback_method = backtosql.Column("video_playback_method", BREAKDOWN, null=True)

    country = backtosql.Column("country", BREAKDOWN, null=True)
    state = backtosql.Column("state", BREAKDOWN, null=True)
    dma = backtosql.Column("dma", BREAKDOWN, null=True)

    age = backtosql.Column("age", BREAKDOWN, null=True)
    gender = backtosql.Column("gender", BREAKDOWN, null=True)
    age_gender = backtosql.Column("age_gender", BREAKDOWN, null=True)

    # The basics
    clicks = backtosql.TemplateColumn("part_sum.sql", {"column_name": "clicks"}, AGGREGATE)
    impressions = backtosql.TemplateColumn("part_sum.sql", {"column_name": "impressions"}, AGGREGATE)

    # Costs
    media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "cost_nano"}, AGGREGATE)
    local_media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "local_cost_nano"}, AGGREGATE)
    e_media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "effective_cost_nano"}, AGGREGATE)
    local_e_media_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_effective_cost_nano"}, AGGREGATE
    )  # noqa

    data_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "data_cost_nano"}, AGGREGATE)
    local_data_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "local_data_cost_nano"}, AGGREGATE)
    e_data_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "effective_data_cost_nano"}, AGGREGATE)
    local_e_data_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_effective_data_cost_nano"}, AGGREGATE
    )  # noqa

    at_cost = backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, group=AGGREGATE)
    local_at_cost = backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, group=AGGREGATE)
    et_cost = backtosql.TemplateColumn("part_2sum_nano.sql", ET_COST_COLUMNS, group=AGGREGATE)
    local_et_cost = backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_ET_COST_COLUMNS, group=AGGREGATE)
    etf_cost = backtosql.TemplateColumn("part_3sum_nano.sql", ETF_COST_COLUMNS, group=AGGREGATE)
    local_etf_cost = backtosql.TemplateColumn("part_3sum_nano.sql", LOCAL_ETF_COST_COLUMNS, group=AGGREGATE)
    etfm_cost = backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, group=AGGREGATE)
    local_etfm_cost = backtosql.TemplateColumn("part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, group=AGGREGATE)

    license_fee = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "license_fee_nano"}, AGGREGATE)
    local_license_fee = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_license_fee_nano"}, AGGREGATE
    )  # noqa
    margin = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "margin_nano"}, AGGREGATE)
    local_margin = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "local_margin_nano"}, AGGREGATE)

    # Legacy costs
    # FIXME: Remove the following columns after new margins are completely migrated to
    total_cost = backtosql.TemplateColumn("part_4sum_nano.sql", ATFM_COST_COLUMNS, group=AGGREGATE)
    local_total_cost = backtosql.TemplateColumn("part_4sum_nano.sql", LOCAL_ATFM_COST_COLUMNS, group=AGGREGATE)
    billing_cost = backtosql.TemplateColumn("part_3sum_nano.sql", ETF_COST_COLUMNS, group=AGGREGATE)
    local_billing_cost = backtosql.TemplateColumn("part_3sum_nano.sql", LOCAL_ETF_COST_COLUMNS, group=AGGREGATE)
    agency_cost = backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, group=AGGREGATE)
    local_agency_cost = backtosql.TemplateColumn("part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, group=AGGREGATE)

    # Derivates
    ctr = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "clicks", "divisor": "impressions", "divisor_modifier": "0.01"}, AGGREGATE
    )

    _context = {"divisor": "clicks", "divisor_modifier": converters.CURRENCY_TO_NANO}
    et_cpc = backtosql.TemplateColumn("part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE)
    local_et_cpc = backtosql.TemplateColumn("part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE)
    etfm_cpc = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_cpc = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    cpc = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE)
    local_cpc = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE)

    _context = {"divisor": "impressions", "divisor_modifier": converters.CURRENCY_TO_NANO * 0.001}
    et_cpm = backtosql.TemplateColumn("part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE)
    local_et_cpm = backtosql.TemplateColumn("part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE)
    etfm_cpm = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_cpm = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    cpm = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE)
    local_cpm = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE)

    # Postclick acquisition fields
    visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "visits"}, AGGREGATE)
    pageviews = backtosql.TemplateColumn("part_sum.sql", {"column_name": "pageviews"}, AGGREGATE)
    click_discrepancy = backtosql.TemplateColumn("part_click_discrepancy.sql", None, AGGREGATE)

    # Postclick engagement fields
    new_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATE)
    percent_new_users = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "new_visits", "divisor": "visits", "divisor_modifier": "0.01"}, AGGREGATE
    )  # noqa
    bounce_rate = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "bounced_visits", "divisor": "visits", "divisor_modifier": "0.01"}, AGGREGATE
    )  # noqa
    pv_per_visit = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "pageviews", "divisor": "visits"}, AGGREGATE
    )  # noqa
    avg_tos = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "total_time_on_site", "divisor": "visits"}, AGGREGATE
    )  # noqa
    returning_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "returning_users"}, AGGREGATE)
    unique_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "users"}, AGGREGATE)
    new_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATE)
    bounced_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "bounced_visits"}, AGGREGATE)
    total_seconds = backtosql.TemplateColumn("part_sum.sql", {"column_name": "total_time_on_site"}, AGGREGATE)
    non_bounced_visits = backtosql.TemplateColumn("part_non_bounced_visits.sql", group=AGGREGATE)
    total_pageviews = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "pageviews"}, group=AGGREGATE
    )  # TODO duplicate with 'pageviews'  # noqa

    # Average costs per metrics
    _context = {"divisor": "total_time_on_site", "divisor_modifier": converters.CURRENCY_TO_NANO / 60.0}
    avg_et_cost_per_minute = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_et_cost_per_minute = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    avg_etfm_cost_per_minute = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_etfm_cost_per_minute = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    avg_cost_per_minute = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE)
    local_avg_cost_per_minute = backtosql.TemplateColumn(
        "part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE
    )  # noqa

    avg_et_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_avg_et_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )  # noqa
    local_avg_et_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_local_avg_et_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )  # noqa
    avg_etfm_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_avg_etfm_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )  # noqa
    local_avg_etfm_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_local_avg_etfm_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    avg_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_avg_a_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )  # noqa
    local_avg_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_local_avg_a_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )  # noqa

    _context = {"divisor": "pageviews", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_et_cost_per_pageview = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_et_cost_per_pageview = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    avg_etfm_cost_per_pageview = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_etfm_cost_per_pageview = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    avg_cost_per_pageview = backtosql.TemplateColumn(
        "part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_cost_per_pageview = backtosql.TemplateColumn(
        "part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE
    )  # noqa

    _context = {"divisor": "new_visits", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_et_cost_for_new_visitor = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_et_cost_for_new_visitor = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    avg_etfm_cost_for_new_visitor = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_etfm_cost_for_new_visitor = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    avg_cost_for_new_visitor = backtosql.TemplateColumn(
        "part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_cost_for_new_visitor = backtosql.TemplateColumn(
        "part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE
    )  # noqa

    _context = {"divisor": "visits", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_et_cost_per_visit = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_et_cost_per_visit = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    avg_etfm_cost_per_visit = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_avg_etfm_cost_per_visit = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    avg_cost_per_visit = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE)
    local_avg_cost_per_visit = backtosql.TemplateColumn(
        "part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE
    )  # noqa

    # Video
    video_start = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_start"}, AGGREGATE)
    video_first_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_first_quartile"}, AGGREGATE)
    video_midpoint = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_midpoint"}, AGGREGATE)
    video_third_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_third_quartile"}, AGGREGATE)
    video_complete = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_complete"}, AGGREGATE)
    video_progress_3s = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_progress_3s"}, AGGREGATE)

    # Video  derivates
    _context = {"divisor": "video_first_quartile", "divisor_modifier": converters.CURRENCY_TO_NANO}
    video_et_cpv = backtosql.TemplateColumn("part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE)
    local_video_et_cpv = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    video_etfm_cpv = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_video_etfm_cpv = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    video_cpv = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE)
    local_video_cpv = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE)

    _context = {"divisor": "video_complete", "divisor_modifier": converters.CURRENCY_TO_NANO}
    video_et_cpcv = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_video_et_cpcv = backtosql.TemplateColumn(
        "part_2sumdiv.sql", dict_join(_context, LOCAL_ET_COST_COLUMNS), AGGREGATE
    )  # noqa
    video_etfm_cpcv = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    local_video_etfm_cpcv = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )  # noqa
    # FIXME: Remove the following columns after new margins are completely migrated to
    video_cpcv = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, A_COST_COLUMNS), AGGREGATE)
    local_video_cpcv = backtosql.TemplateColumn("part_sumdiv.sql", dict_join(_context, LOCAL_A_COST_COLUMNS), AGGREGATE)


class MVTouchpointConversions(BreakdownsBase):
    device_type = backtosql.Column("device_type", BREAKDOWN)
    device_os = backtosql.Column("device_os", BREAKDOWN)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN)
    placement_medium = backtosql.Column("placement_medium", BREAKDOWN)

    country = backtosql.Column("country", BREAKDOWN)
    state = backtosql.Column("state", BREAKDOWN)
    dma = backtosql.Column("dma", BREAKDOWN)

    slug = backtosql.Column("slug", BREAKDOWN)
    window = backtosql.Column("conversion_window", BREAKDOWN, alias='"window"')  # window is reserved word in PostgreSQL

    count = backtosql.TemplateColumn(
        "part_sum_conversion_type.sql",
        {"column_name": "conversion_count", "conversion_type": dash.constants.ConversionType.CLICK},
        AGGREGATE,
    )
    conversion_value = backtosql.TemplateColumn(
        "part_sum_nano_conversion_type.sql",
        {"column_name": "conversion_value_nano", "conversion_type": dash.constants.ConversionType.CLICK},
        AGGREGATE,
    )  # noqa
    count_view = backtosql.TemplateColumn(
        "part_sum_conversion_type.sql",
        {"column_name": "conversion_count", "conversion_type": dash.constants.ConversionType.VIEW},
        AGGREGATE,
    )
    conversion_value_view = backtosql.TemplateColumn(
        "part_sum_nano_conversion_type.sql",
        {"column_name": "conversion_value_nano", "conversion_type": dash.constants.ConversionType.VIEW},
        AGGREGATE,
    )  # noqa


class MVConversions(BreakdownsBase):
    slug = backtosql.Column("slug", BREAKDOWN)
    count = backtosql.TemplateColumn("part_sum.sql", {"column_name": "conversion_count"}, AGGREGATE)


class MVJointMaster(MVMaster):
    yesterday_at_cost = backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_yesterday_at_cost = backtosql.TemplateColumn(
        "part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )  # noqa
    yesterday_et_cost = backtosql.TemplateColumn("part_2sum_nano.sql", ET_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_yesterday_et_cost = backtosql.TemplateColumn(
        "part_2sum_nano.sql", LOCAL_ET_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )  # noqa
    yesterday_etfm_cost = backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_yesterday_etfm_cost = backtosql.TemplateColumn(
        "part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )  # noqa

    # FIXME: Remove the following 4 columns after new margins are completely migrated to
    yesterday_cost = backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_yesterday_cost = backtosql.TemplateColumn(
        "part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )  # noqa
    e_yesterday_cost = backtosql.TemplateColumn("part_2sum_nano.sql", ET_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_e_yesterday_cost = backtosql.TemplateColumn(
        "part_2sum_nano.sql", LOCAL_ET_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )  # noqa

    def init_conversion_columns(self, conversion_goals):
        if not conversion_goals:
            return

        # dynamically generate columns based on conversion goals
        for conversion_goal in conversion_goals:
            if conversion_goal.type not in dash.constants.REPORT_GOAL_TYPES:
                continue

            conversion_key = conversion_goal.get_view_key(conversion_goals)
            self.add_column(
                backtosql.TemplateColumn(
                    "part_conversion_goal.sql",
                    {"goal_id": conversion_goal.get_stats_key()},
                    alias=conversion_key,
                    group=CONVERSION_AGGREGATES,
                )
            )

            # FIXME: Remove the following columns after new margins are completely migrated to
            self.add_column(
                backtosql.TemplateColumn(
                    "part_avg_cost_per_conversion_goal.sql",
                    {"cost_column": "e_media_cost", "conversion_key": conversion_key},
                    alias="avg_cost_per_" + conversion_key,
                    group=AFTER_JOIN_AGGREGATES,
                )
            )
            self.add_column(
                backtosql.TemplateColumn(
                    "part_avg_cost_per_conversion_goal.sql",
                    {"cost_column": "local_e_media_cost", "conversion_key": conversion_key},
                    alias="local_avg_cost_per_" + conversion_key,
                    group=AFTER_JOIN_AGGREGATES,
                )
            )

            self.add_column(
                backtosql.TemplateColumn(
                    "part_avg_cost_per_conversion_goal.sql",
                    {"cost_column": "et_cost", "conversion_key": conversion_key},
                    alias="avg_et_cost_per_" + conversion_key,
                    group=AFTER_JOIN_AGGREGATES,
                )
            )
            self.add_column(
                backtosql.TemplateColumn(
                    "part_avg_cost_per_conversion_goal.sql",
                    {"cost_column": "local_et_cost", "conversion_key": conversion_key},
                    alias="local_avg_et_cost_per_" + conversion_key,
                    group=AFTER_JOIN_AGGREGATES,
                )
            )
            self.add_column(
                backtosql.TemplateColumn(
                    "part_avg_cost_per_conversion_goal.sql",
                    {"cost_column": "etfm_cost", "conversion_key": conversion_key},
                    alias="avg_etfm_cost_per_" + conversion_key,
                    group=AFTER_JOIN_AGGREGATES,
                )
            )
            self.add_column(
                backtosql.TemplateColumn(
                    "part_avg_cost_per_conversion_goal.sql",
                    {"cost_column": "local_etfm_cost", "conversion_key": conversion_key},
                    alias="local_avg_etfm_cost_per_" + conversion_key,
                    group=AFTER_JOIN_AGGREGATES,
                )
            )

    def init_pixel_columns(self, pixels):
        if not pixels:
            return

        click_conversion_windows = sorted(dash.constants.ConversionWindowsLegacy.get_all())
        view_conversion_windows = sorted(dash.constants.ConversionWindows.get_all())

        self._generate_pixel_columns(pixels, click_conversion_windows, dash.constants.ConversionType.CLICK)
        self._generate_pixel_columns(
            pixels, view_conversion_windows, dash.constants.ConversionType.VIEW, suffix="_view"
        )

    def _generate_pixel_columns(self, pixels, conversion_windows, conversion_type, suffix=None):
        for pixel in pixels:
            for conversion_window in conversion_windows:
                pixel_key = pixel.get_view_key(conversion_window) + (suffix or "")

                self.add_column(
                    backtosql.TemplateColumn(
                        "part_touchpointconversion_goal.sql",
                        {
                            "account_id": pixel.account_id,
                            "slug": pixel.slug,
                            "window": conversion_window,
                            "type": conversion_type,
                        },
                        alias=pixel_key,
                        group=TOUCHPOINTS_AGGREGATES,
                    )
                )

                self.add_column(
                    backtosql.TemplateColumn(
                        "part_total_conversion_value.sql",
                        {
                            "account_id": pixel.account_id,
                            "slug": pixel.slug,
                            "window": conversion_window,
                            "type": conversion_type,
                        },
                        alias="total_conversion_value_" + pixel_key,
                        group=TOUCHPOINTS_AGGREGATES,
                    )
                )

                # FIXME: Remove the following columns after new margins are completely migrated to
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_avg_cost_per_conversion_goal.sql",
                        {"cost_column": "e_media_cost", "conversion_key": pixel_key},  # noqa
                        alias="avg_cost_per_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_avg_cost_per_conversion_goal.sql",
                        {"cost_column": "local_e_media_cost", "conversion_key": pixel_key},  # noqa
                        alias="local_avg_cost_per_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )

                self.add_column(
                    backtosql.TemplateColumn(
                        "part_avg_cost_per_conversion_goal.sql",
                        {"cost_column": "et_cost", "conversion_key": pixel_key},
                        alias="avg_et_cost_per_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_avg_cost_per_conversion_goal.sql",
                        {"cost_column": "local_et_cost", "conversion_key": pixel_key},
                        alias="local_avg_et_cost_per_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_avg_cost_per_conversion_goal.sql",
                        {"cost_column": "etfm_cost", "conversion_key": pixel_key},
                        alias="avg_etfm_cost_per_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_avg_cost_per_conversion_goal.sql",
                        {"cost_column": "local_etfm_cost", "conversion_key": pixel_key},
                        alias="local_avg_etfm_cost_per_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )

                # FIXME: Remove the following column after new margins are completely migrated to
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_roas.sql",
                        {"cost_column": "local_e_media_cost", "conversion_key": pixel_key},
                        alias="roas_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )

                self.add_column(
                    backtosql.TemplateColumn(
                        "part_roas.sql",
                        {"cost_column": "local_et_cost", "conversion_key": pixel_key},
                        alias="et_roas_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )
                self.add_column(
                    backtosql.TemplateColumn(
                        "part_roas.sql",
                        {"cost_column": "local_etfm_cost", "conversion_key": pixel_key},
                        alias="etfm_roas_" + pixel_key,
                        group=AFTER_JOIN_AGGREGATES,
                    )
                )

    def init_performance_columns(
        self,
        campaign_goals,
        campaign_goal_values,
        conversion_goals,
        pixels,
        supports_conversions=True,
        supports_touchpoints=True,
    ):
        if not campaign_goals:
            return

        map_camp_goal_vals = {x.campaign_goal_id: x for x in campaign_goal_values or []}
        map_conversion_goals = {x.id: x for x in conversion_goals or []}
        pixel_ids = [x.id for x in pixels] if pixels else []

        # FIXME: circular import
        import dash.campaign_goals

        for campaign_goal in campaign_goals:
            conversion_key = None
            metric_column = None

            if campaign_goal.type == dash.constants.CampaignGoalKPI.CPA:
                if not supports_touchpoints:
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
                # with_local_prefix=False because USD metric values should be used to calculate performance
                primary_metric_map = dash.campaign_goals.get_goal_to_primary_metric_map(
                    campaign_goal.campaign.account.uses_bcm_v2, with_local_prefix=False
                )
                metric_column = primary_metric_map[campaign_goal.type]
                column_group = AFTER_JOIN_AGGREGATES

            is_cost_dependent = campaign_goal.type in dash.campaign_goals.COST_DEPENDANT_GOALS
            is_inverse_performance = campaign_goal.type in dash.campaign_goals.INVERSE_PERFORMANCE_CAMPAIGN_GOALS

            campaign_goal_value = map_camp_goal_vals.get(campaign_goal.pk)
            if campaign_goal_value and campaign_goal_value.value:
                planned_value = campaign_goal_value.value
            else:
                planned_value = "NULL"

            # FIXME: Remove the following column after new margins are completely migrated to
            self.add_column(
                backtosql.TemplateColumn(
                    "part_performance.sql",
                    {
                        "is_cost_dependent": is_cost_dependent,
                        "is_inverse_performance": is_inverse_performance,
                        "has_conversion_key": conversion_key is not None,
                        "conversion_key": conversion_key or "0",
                        "planned_value": planned_value,
                        "metric_column": metric_column or "-1",
                        "cost_column": "e_media_cost",
                        "metric_val_decimal_places": dash.campaign_goals.NR_DECIMALS[campaign_goal.type],
                    },
                    alias="performance_" + campaign_goal.get_view_key(),
                    group=column_group,
                )
            )

            self.add_column(
                backtosql.TemplateColumn(
                    "part_performance.sql",
                    {
                        "is_cost_dependent": is_cost_dependent,
                        "is_inverse_performance": is_inverse_performance,
                        "has_conversion_key": conversion_key is not None,
                        "conversion_key": conversion_key or "0",
                        "planned_value": planned_value,
                        "metric_column": metric_column or "-1",
                        "cost_column": "etfm_cost",
                        "metric_val_decimal_places": dash.campaign_goals.NR_DECIMALS[campaign_goal.type],
                    },
                    alias="etfm_performance_" + campaign_goal.get_view_key(),
                    group=column_group,
                )
            )

    def get_query_joint_context(
        self,
        breakdown,
        constraints,
        parents,
        orders,
        offset,
        limit,
        goals,
        views,
        skip_performance_columns=False,
        supports_conversions=False,
        supports_touchpoints=False,
    ):

        # FIXME: temp fix account level publishers view with lots of campaign goals
        skip_performance_columns |= "publisher_id" in breakdown and not set(["campaign_id", "ad_group_id"]) & set(
            constraints.keys()
        )

        constraints, temp_tables = self._constraints_to_temp_tables(constraints)

        if supports_conversions:
            self.init_conversion_columns(goals.conversion_goals)
        if supports_touchpoints:
            self.init_pixel_columns(goals.pixels)

        if not skip_performance_columns:
            self.init_performance_columns(
                goals.campaign_goals,
                goals.campaign_goal_values,
                goals.conversion_goals,
                goals.pixels,
                supports_conversions=supports_conversions,
                supports_touchpoints=supports_touchpoints,
            )

        context = {
            "breakdown": self.get_breakdown(breakdown),
            "partition": self.get_breakdown(stats.constants.get_parent_breakdown(breakdown)),
            "constraints": self.get_constraints(constraints, parents),
            "yesterday_constraints": self.get_constraints(helpers.get_yesterday_constraints(constraints), parents),
            "temp_tables": temp_tables,
            "aggregates": self.get_aggregates(breakdown, views["base"]),
            "yesterday_aggregates": self.select_columns(group=YESTERDAY_AGGREGATES),
            "after_join_aggregates": self.select_columns(group=AFTER_JOIN_AGGREGATES),
            "offset": offset,
            "limit": limit,
            "orders": self.get_order(orders),
            "base_view": views["base"],
            "yesterday_view": views["yesterday"],
        }

        if supports_conversions:
            context.update(
                {
                    "conversions_constraints": self.get_constraints(constraints, parents),
                    "conversions_aggregates": self.select_columns(group=CONVERSION_AGGREGATES),
                    "conversions_view": views["conversions"],
                }
            )

        if supports_touchpoints:
            context.update(
                {
                    "touchpoints_constraints": self.get_constraints(constraints, parents),
                    "touchpoints_aggregates": self.select_columns(group=TOUCHPOINTS_AGGREGATES),
                    "touchpoints_view": views["touchpoints"],
                }
            )

        return context
