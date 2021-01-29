import collections
import copy

import backtosql
import dash.constants
import stats.constants
from redshiftapi import helpers
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

AT_COST_COLUMNS = {"column_name1": "cost_nano", "column_name2": "data_cost_nano"}
BT_COST_COLUMNS = {"column_name1": "base_effective_cost_nano", "column_name2": "base_effective_data_cost_nano"}
ET_COST_COLUMNS = {
    "column_name1": "effective_cost_nano",
    "column_name2": "effective_data_cost_nano",
    # service fee already included in effective cost
}
ETF_COST_COLUMNS = {
    "column_name1": "effective_cost_nano",
    "column_name2": "effective_data_cost_nano",
    "column_name3": "license_fee_nano",
    # service fee already included in effective cost
}
ETFM_COST_COLUMNS = {
    "column_name1": "effective_cost_nano",
    "column_name2": "effective_data_cost_nano",
    "column_name3": "license_fee_nano",
    "column_name4": "margin_nano",
    # service fee already included in effective cost
}

LOCAL_AT_COST_COLUMNS = {"column_name1": "local_cost_nano", "column_name2": "local_data_cost_nano"}
LOCAL_BT_COST_COLUMNS = {
    "column_name1": "local_base_effective_cost_nano",
    "column_name2": "local_base_effective_data_cost_nano",
}
LOCAL_ET_COST_COLUMNS = {
    "column_name1": "local_effective_cost_nano",
    "column_name2": "local_effective_data_cost_nano",
    # service fee already included in effective cost
}
LOCAL_ETF_COST_COLUMNS = {
    "column_name1": "local_effective_cost_nano",
    "column_name2": "local_effective_data_cost_nano",
    "column_name3": "local_license_fee_nano",
    # service fee already included in effective cost
}
LOCAL_ETFM_COST_COLUMNS = {
    "column_name1": "local_effective_cost_nano",
    "column_name2": "local_effective_data_cost_nano",
    "column_name3": "local_license_fee_nano",
    "column_name4": "local_margin_nano",
    # service fee already included in effective cost
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
    placement = backtosql.Column("placement", BREAKDOWN)

    publisher_id = backtosql.TemplateColumn("part_publisher_id.sql")
    placement_id = backtosql.TemplateColumn("part_placement_id.sql")
    placement_type = backtosql.TemplateColumn("part_max.sql", {"column_name": "placement_type"})

    def get_breakdown(self, breakdown):
        """ Selects breakdown subset of columns """

        if "publisher_id" in breakdown:
            publisher_id_idx = breakdown.index("publisher_id")
            breakdown = breakdown[:publisher_id_idx] + ["publisher", "source_id"] + breakdown[publisher_id_idx + 1 :]
        if "placement_id" in breakdown:
            placement = breakdown.index("placement_id")
            breakdown = breakdown[:placement] + ["publisher", "placement", "source_id"] + breakdown[placement + 1 :]

        # remove duplicated dimensions
        breakdown = list(collections.OrderedDict(list(zip(breakdown, breakdown))).keys())

        return self.select_columns(subset=breakdown)

    def get_order(self, order_list):
        return [self.get_column(x).as_order(x, nulls="last") for x in order_list]

    def get_aggregates(self, breakdown):
        """ Returns all the aggregate columns """
        columns = self.select_columns(group=AGGREGATE)

        if "placement_id" in breakdown:
            columns.append(self.placement_type)

        return columns

    def get_additional_columns(self, breakdown):
        """ additional top-level columns """
        columns = []

        if "publisher_id" in breakdown:
            columns.append(self.publisher_id)

        if "placement_id" in breakdown:
            columns.append(self.placement_id)

        return columns

    def get_constraints(self, constraints, parents):
        constraints = copy.copy(constraints)

        publisher = constraints.pop("publisher_id", None)
        publisher__neq = constraints.pop("publisher_id__neq", None)

        placement = constraints.pop("placement_id", None)
        placement__neq = constraints.pop("placement_id__neq", None)

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

        if placement is not None:
            if not placement:
                # this is the case when we want to query blacklisted placements but there are no blacklisted placements
                # modify constraints to not return anything
                constraints = backtosql.Q.none(self)
            else:
                constraints = constraints & self.get_parent_constraints([{"placement_id": x} for x in placement])

        if placement__neq:
            constraints = constraints & ~self.get_parent_constraints([{"placement_id": x} for x in placement__neq])

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
            "aggregates": self.get_aggregates(breakdown),
            "additional_columns": self.get_additional_columns(breakdown),
            "constraints": self.get_constraints(constraints, parents),
            "temp_tables": temp_tables,
            "view": view,
            "orders": self.get_order(orders),
        }

    def get_query_counts_context(self, breakdown, constraints, parents, view):
        constraints, temp_tables = self._constraints_to_temp_tables(constraints)
        return {
            "parent_breakdown": self.get_breakdown(stats.constants.get_parent_breakdown(breakdown)),
            "breakdown": self.get_breakdown(breakdown),
            "constraints": self.get_constraints(constraints, parents),
            "temp_tables": temp_tables,
            "view": view,
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
            "yesterday_etfm_cost",
            "local_yesterday_etfm_cost",
        ]
        self.add_column(backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, alias="yesterday_at_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, alias="local_yesterday_at_cost")
        )
        self.add_column(backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, alias="yesterday_etfm_cost"))
        self.add_column(
            backtosql.TemplateColumn("part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, alias="local_yesterday_etfm_cost")
        )

        return {
            "breakdown": self.get_breakdown(breakdown),
            "aggregates": self.select_columns(aggregates),
            "additional_columns": self.get_additional_columns(breakdown),
            "constraints": self.get_constraints(constraints, parents),
            "temp_tables": temp_tables,
            "view": view,
            "orders": self.get_order(orders),
        }


class MVMaster(BreakdownsBase):
    # Breakdowns
    # NOTE: null_type parameter is important for fields on which conversions are joined, because null != null in SQL. Should match with MVTouchpointConversions
    device_type = backtosql.Column("device_type", BREAKDOWN, null_type=int)
    device_os = backtosql.Column("device_os", BREAKDOWN, null_type=str)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN, null_type=str)
    environment = backtosql.Column("environment", BREAKDOWN, null_type=str)
    browser = backtosql.Column("browser", BREAKDOWN, null_type=str)
    connection_type = backtosql.Column("connection_type", BREAKDOWN, null_type=str)

    zem_placement_type = backtosql.Column("zem_placement_type", BREAKDOWN)
    video_playback_method = backtosql.Column("video_playback_method", BREAKDOWN)

    country = backtosql.Column("country", BREAKDOWN, null_type=str)
    region = backtosql.Column("state", BREAKDOWN, null_type=str)
    dma = backtosql.Column("dma", BREAKDOWN, null_type=int)

    age = backtosql.Column("age", BREAKDOWN)
    gender = backtosql.Column("gender", BREAKDOWN)
    age_gender = backtosql.Column("age_gender", BREAKDOWN)

    # The basics
    clicks = backtosql.TemplateColumn("part_sum.sql", {"column_name": "clicks"}, AGGREGATE)
    impressions = backtosql.TemplateColumn("part_sum.sql", {"column_name": "impressions"}, AGGREGATE)

    # Actual costs
    media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "cost_nano"}, AGGREGATE)
    local_media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "local_cost_nano"}, AGGREGATE)
    data_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "data_cost_nano"}, AGGREGATE)
    local_data_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "local_data_cost_nano"}, AGGREGATE)
    at_cost = backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, group=AGGREGATE)
    local_at_cost = backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, group=AGGREGATE)

    # Base effective costs
    b_media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "base_effective_cost_nano"}, AGGREGATE)
    local_b_media_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_base_effective_cost_nano"}, AGGREGATE
    )
    b_data_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "base_effective_data_cost_nano"}, AGGREGATE
    )
    local_b_data_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_base_effective_data_cost_nano"}, AGGREGATE
    )
    bt_cost = backtosql.TemplateColumn("part_2sum_nano.sql", BT_COST_COLUMNS, group=AGGREGATE)
    local_bt_cost = backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_BT_COST_COLUMNS, group=AGGREGATE)

    # Effective costs
    e_media_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "effective_cost_nano"}, AGGREGATE)
    local_e_media_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_effective_cost_nano"}, AGGREGATE
    )
    e_data_cost = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "effective_data_cost_nano"}, AGGREGATE)
    local_e_data_cost = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_effective_data_cost_nano"}, AGGREGATE
    )
    et_cost = backtosql.TemplateColumn("part_2sum_nano.sql", ET_COST_COLUMNS, group=AGGREGATE)
    local_et_cost = backtosql.TemplateColumn("part_2sum_nano.sql", LOCAL_ET_COST_COLUMNS, group=AGGREGATE)
    etf_cost = backtosql.TemplateColumn("part_3sum_nano.sql", ETF_COST_COLUMNS, group=AGGREGATE)
    local_etf_cost = backtosql.TemplateColumn("part_3sum_nano.sql", LOCAL_ETF_COST_COLUMNS, group=AGGREGATE)
    etfm_cost = backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, group=AGGREGATE)
    local_etfm_cost = backtosql.TemplateColumn("part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, group=AGGREGATE)

    # Fees
    service_fee = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "service_fee_nano"}, AGGREGATE)
    local_service_fee = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_service_fee_nano"}, AGGREGATE
    )
    license_fee = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "license_fee_nano"}, AGGREGATE)
    local_license_fee = backtosql.TemplateColumn(
        "part_sum_nano.sql", {"column_name": "local_license_fee_nano"}, AGGREGATE
    )
    margin = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "margin_nano"}, AGGREGATE)
    local_margin = backtosql.TemplateColumn("part_sum_nano.sql", {"column_name": "local_margin_nano"}, AGGREGATE)

    # Derivatives
    ctr = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "clicks", "divisor": "impressions", "divisor_modifier": "0.01"}, AGGREGATE
    )

    _context = {"divisor": "clicks", "divisor_modifier": converters.CURRENCY_TO_NANO}
    etfm_cpc = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_cpc = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    _context = {"divisor": "impressions", "divisor_modifier": converters.CURRENCY_TO_NANO * 0.001}
    etfm_cpm = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_cpm = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    # Postclick acquisition fields
    visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "visits"}, AGGREGATE)
    pageviews = backtosql.TemplateColumn("part_sum.sql", {"column_name": "pageviews"}, AGGREGATE)
    click_discrepancy = backtosql.TemplateColumn("part_click_discrepancy.sql", None, AGGREGATE)

    # Postclick engagement fields
    new_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATE)
    percent_new_users = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "new_visits", "divisor": "visits", "divisor_modifier": "0.01"}, AGGREGATE
    )
    bounce_rate = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "bounced_visits", "divisor": "visits", "divisor_modifier": "0.01"}, AGGREGATE
    )
    pv_per_visit = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "pageviews", "divisor": "visits"}, AGGREGATE
    )
    avg_tos = backtosql.TemplateColumn(
        "part_sumdiv.sql", {"column_name": "total_time_on_site", "divisor": "visits"}, AGGREGATE
    )
    returning_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "returning_users"}, AGGREGATE)
    unique_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "users"}, AGGREGATE)
    new_users = backtosql.TemplateColumn("part_sum.sql", {"column_name": "new_visits"}, AGGREGATE)
    bounced_visits = backtosql.TemplateColumn("part_sum.sql", {"column_name": "bounced_visits"}, AGGREGATE)
    total_seconds = backtosql.TemplateColumn("part_sum.sql", {"column_name": "total_time_on_site"}, AGGREGATE)
    non_bounced_visits = backtosql.TemplateColumn("part_non_bounced_visits.sql", group=AGGREGATE)
    total_pageviews = backtosql.TemplateColumn(
        "part_sum.sql", {"column_name": "pageviews"}, group=AGGREGATE
    )  # TODO duplicate with 'pageviews'

    # Average costs per metrics
    _context = {"divisor": "total_time_on_site", "divisor_modifier": converters.CURRENCY_TO_NANO / 60.0}
    avg_etfm_cost_per_minute = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )
    local_avg_etfm_cost_per_minute = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    avg_etfm_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_avg_etfm_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )
    local_avg_etfm_cost_per_non_bounced_visit = backtosql.TemplateColumn(
        "part_local_avg_etfm_cost_per_non_bounced_visit.sql", group=AGGREGATE
    )

    _context = {"divisor": "pageviews", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_etfm_cost_per_pageview = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )
    local_avg_etfm_cost_per_pageview = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    _context = {"divisor": "new_visits", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_etfm_cost_per_new_visitor = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )
    local_avg_etfm_cost_per_new_visitor = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    _context = {"divisor": "visits", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_etfm_cost_per_visit = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )
    local_avg_etfm_cost_per_visit = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    _context = {"divisor": "users", "divisor_modifier": converters.CURRENCY_TO_NANO}
    avg_etfm_cost_per_unique_user = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE
    )
    local_avg_etfm_cost_per_unique_user = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    # Video
    video_start = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_start"}, AGGREGATE)
    video_first_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_first_quartile"}, AGGREGATE)
    video_midpoint = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_midpoint"}, AGGREGATE)
    video_third_quartile = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_third_quartile"}, AGGREGATE)
    video_complete = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_complete"}, AGGREGATE)
    video_progress_3s = backtosql.TemplateColumn("part_sum.sql", {"column_name": "video_progress_3s"}, AGGREGATE)

    # Video derivatives
    _context = {"divisor": "video_first_quartile", "divisor_modifier": converters.CURRENCY_TO_NANO}
    video_etfm_cpv = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_video_etfm_cpv = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    _context = {"divisor": "video_complete", "divisor_modifier": converters.CURRENCY_TO_NANO}
    video_etfm_cpcv = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_video_etfm_cpcv = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    video_start_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "video_start", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    video_first_quartile_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "video_first_quartile", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    video_midpoint_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "video_midpoint", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    video_third_quartile_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "video_third_quartile", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    video_complete_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "video_complete", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    video_progress_3s_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "video_progress_3s", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )

    # MRC50 viewability
    mrc50_measurable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc50_measurable"}, AGGREGATE)
    mrc50_viewable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc50_viewable"}, AGGREGATE)
    mrc50_non_measurable = backtosql.TemplateColumn(
        "part_sumdiff.sql", {"column_name1": "impressions", "column_name2": "mrc50_measurable"}, AGGREGATE
    )
    mrc50_non_viewable = backtosql.TemplateColumn(
        "part_sumdiff.sql", {"column_name1": "mrc50_measurable", "column_name2": "mrc50_viewable"}, AGGREGATE
    )
    mrc50_measurable_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "mrc50_measurable", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    mrc50_viewable_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "mrc50_viewable", "divisor": "mrc50_measurable", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    mrc50_viewable_distribution = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "mrc50_viewable", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    _context = {"divisor": "impressions", "divisor_modifier": "0.01"}
    mrc50_non_measurable_distribution = backtosql.TemplateColumn(
        "part_sumdiffdiv.sql",
        dict_join(_context, {"column_name1": "impressions", "column_name2": "mrc50_measurable"}),
        AGGREGATE,
    )
    mrc50_non_viewable_distribution = backtosql.TemplateColumn(
        "part_sumdiffdiv.sql",
        dict_join(_context, {"column_name1": "mrc50_measurable", "column_name2": "mrc50_viewable"}),
        AGGREGATE,
    )
    _context = {"divisor": "mrc50_viewable", "divisor_modifier": converters.CURRENCY_TO_NANO * 0.001}
    etfm_mrc50_vcpm = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_mrc50_vcpm = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    # MRC100 viewability
    mrc100_measurable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc100_measurable"}, AGGREGATE)
    mrc100_viewable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "mrc100_viewable"}, AGGREGATE)
    mrc100_non_measurable = backtosql.TemplateColumn(
        "part_sumdiff.sql", {"column_name1": "impressions", "column_name2": "mrc100_measurable"}, AGGREGATE
    )
    mrc100_non_viewable = backtosql.TemplateColumn(
        "part_sumdiff.sql", {"column_name1": "mrc100_measurable", "column_name2": "mrc100_viewable"}, AGGREGATE
    )
    mrc100_measurable_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "mrc100_measurable", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    mrc100_viewable_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "mrc100_viewable", "divisor": "mrc100_measurable", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    mrc100_viewable_distribution = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "mrc100_viewable", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    _context = {"divisor": "impressions", "divisor_modifier": "0.01"}
    mrc100_non_measurable_distribution = backtosql.TemplateColumn(
        "part_sumdiffdiv.sql",
        dict_join(_context, {"column_name1": "impressions", "column_name2": "mrc100_measurable"}),
        AGGREGATE,
    )
    mrc100_non_viewable_distribution = backtosql.TemplateColumn(
        "part_sumdiffdiv.sql",
        dict_join(_context, {"column_name1": "mrc100_measurable", "column_name2": "mrc100_viewable"}),
        AGGREGATE,
    )
    _context = {"divisor": "mrc100_viewable", "divisor_modifier": converters.CURRENCY_TO_NANO * 0.001}
    etfm_mrc100_vcpm = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_mrc100_vcpm = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )

    # VAST4 viewability
    vast4_measurable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "vast4_measurable"}, AGGREGATE)
    vast4_viewable = backtosql.TemplateColumn("part_sum.sql", {"column_name": "vast4_viewable"}, AGGREGATE)
    vast4_non_measurable = backtosql.TemplateColumn(
        "part_sumdiff.sql", {"column_name1": "impressions", "column_name2": "vast4_measurable"}, AGGREGATE
    )
    vast4_non_viewable = backtosql.TemplateColumn(
        "part_sumdiff.sql", {"column_name1": "vast4_measurable", "column_name2": "vast4_viewable"}, AGGREGATE
    )
    vast4_measurable_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "vast4_measurable", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    vast4_viewable_percent = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "vast4_viewable", "divisor": "vast4_measurable", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    vast4_viewable_distribution = backtosql.TemplateColumn(
        "part_sumdiv.sql",
        {"column_name": "vast4_viewable", "divisor": "impressions", "divisor_modifier": "0.01"},
        AGGREGATE,
    )
    _context = {"divisor": "impressions", "divisor_modifier": "0.01"}
    vast4_non_measurable_distribution = backtosql.TemplateColumn(
        "part_sumdiffdiv.sql",
        dict_join(_context, {"column_name1": "impressions", "column_name2": "vast4_measurable"}),
        AGGREGATE,
    )
    vast4_non_viewable_distribution = backtosql.TemplateColumn(
        "part_sumdiffdiv.sql",
        dict_join(_context, {"column_name1": "vast4_measurable", "column_name2": "vast4_viewable"}),
        AGGREGATE,
    )
    _context = {"divisor": "vast4_viewable", "divisor_modifier": converters.CURRENCY_TO_NANO * 0.001}
    etfm_vast4_vcpm = backtosql.TemplateColumn("part_4sumdiv.sql", dict_join(_context, ETFM_COST_COLUMNS), AGGREGATE)
    local_etfm_vast4_vcpm = backtosql.TemplateColumn(
        "part_4sumdiv.sql", dict_join(_context, LOCAL_ETFM_COST_COLUMNS), AGGREGATE
    )


class MVTouchpointConversions(BreakdownsBase):
    # NOTE: coalesce parameter is important for fields on which conversions are joined, because null != null in SQL. Should match with MVMaster
    device_type = backtosql.Column("device_type", BREAKDOWN, null_type=int)
    device_os = backtosql.Column("device_os", BREAKDOWN, null_type=str)
    device_os_version = backtosql.Column("device_os_version", BREAKDOWN, null_type=str)
    environment = backtosql.Column("environment", BREAKDOWN, null_type=str)
    browser = backtosql.Column("browser", BREAKDOWN, null_type=str)
    connection_type = backtosql.Column("connection_type", BREAKDOWN, null_type=str)

    country = backtosql.Column("country", BREAKDOWN, null_type=str)
    region = backtosql.Column("state", BREAKDOWN, null_type=str)
    dma = backtosql.Column("dma", BREAKDOWN, null_type=int)

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
    )
    count_view = backtosql.TemplateColumn(
        "part_sum_conversion_type.sql",
        {"column_name": "conversion_count", "conversion_type": dash.constants.ConversionType.VIEW},
        AGGREGATE,
    )
    conversion_value_view = backtosql.TemplateColumn(
        "part_sum_nano_conversion_type.sql",
        {"column_name": "conversion_value_nano", "conversion_type": dash.constants.ConversionType.VIEW},
        AGGREGATE,
    )


class MVConversions(BreakdownsBase):
    slug = backtosql.Column("slug", BREAKDOWN)
    count = backtosql.TemplateColumn("part_sum.sql", {"column_name": "conversion_count"}, AGGREGATE)


class MVJointMaster(MVMaster):
    yesterday_at_cost = backtosql.TemplateColumn("part_2sum_nano.sql", AT_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_yesterday_at_cost = backtosql.TemplateColumn(
        "part_2sum_nano.sql", LOCAL_AT_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )
    yesterday_etfm_cost = backtosql.TemplateColumn("part_4sum_nano.sql", ETFM_COST_COLUMNS, group=YESTERDAY_AGGREGATES)
    local_yesterday_etfm_cost = backtosql.TemplateColumn(
        "part_4sum_nano.sql", LOCAL_ETFM_COST_COLUMNS, group=YESTERDAY_AGGREGATES
    )

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

            self.add_column(
                backtosql.TemplateColumn(
                    "part_div.sql",
                    {"column_name": conversion_key, "divisor": "clicks", "divisor_modifier": 0.01},
                    alias="conversion_rate_per_" + conversion_key,
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
        view_conversion_windows = sorted(dash.constants.ConversionWindowsViewthrough.get_all())

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

                if suffix == "_view":
                    self.add_column(
                        backtosql.TemplateColumn(
                            "part_div.sql",
                            {"column_name": pixel_key, "divisor": "impressions", "divisor_modifier": 0.01},
                            alias="conversion_rate_per_" + pixel_key,
                            group=AFTER_JOIN_AGGREGATES,
                        )
                    )
                else:
                    self.add_column(
                        backtosql.TemplateColumn(
                            "part_div.sql",
                            {"column_name": pixel_key, "divisor": "clicks", "divisor_modifier": 0.01},
                            alias="conversion_rate_per_" + pixel_key,
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
                primary_metric_map = dash.campaign_goals.get_goal_to_primary_metric_map(with_local_prefix=False)
                metric_column = primary_metric_map[campaign_goal.type]
                column_group = AFTER_JOIN_AGGREGATES

            is_cost_dependent = campaign_goal.type in dash.campaign_goals.COST_DEPENDANT_GOALS
            is_inverse_performance = campaign_goal.type in dash.campaign_goals.INVERSE_PERFORMANCE_CAMPAIGN_GOALS

            campaign_goal_value = map_camp_goal_vals.get(campaign_goal.pk)
            if campaign_goal_value and campaign_goal_value.value:
                planned_value = campaign_goal_value.value
            else:
                planned_value = "NULL"

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
            "aggregates": self.get_aggregates(breakdown),
            "yesterday_aggregates": self.select_columns(group=YESTERDAY_AGGREGATES),
            "after_join_aggregates": self.select_columns(group=AFTER_JOIN_AGGREGATES),
            "additional_columns": self.get_additional_columns(breakdown),
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
