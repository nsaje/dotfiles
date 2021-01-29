import datetime
from typing import Any
from typing import Sequence

from django.conf import settings

import automation.rules.constants
import backtosql
import core.models
import redshiftapi.db
import redshiftapi.models
import redshiftapi.view_selector
import utils.converters
import utils.dates_helper
import utils.dict_helper

QUERY_LIMITATION_TARGET_TYPES = [
    automation.rules.constants.TargetType.PUBLISHER,
    automation.rules.constants.TargetType.PLACEMENT,
]
QUERY_LIMITATION_COLUMN = "impressions"
QUERY_LIMITATION_THRESHOLD = 1000


def query(target_type: int, ad_groups: Sequence[core.models.AdGroup]) -> Sequence[Any]:
    if not ad_groups:
        return []

    sql = _get_target_type_sql(target_type, ad_groups)
    rows = redshiftapi.db.execute_query(
        sql, [], _get_target_type_query_name(target_type), db_cluster=settings.STATS_DB_HOT_CLUSTER
    )

    return rows


def _get_target_type_sql(target_type: int, ad_groups: Sequence[core.models.AdGroup]) -> str:
    local_today = utils.dates_helper.local_today()

    target_type_columns = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    breakdown_columns = ["ad_group_id"]
    aggregate_columns = [
        "clicks",
        "impressions",
        "local_etfm_cost",
        "ctr",
        "local_etfm_cpc",
        "local_etfm_cpm",
        "visits",
        "pageviews",
        "click_discrepancy",
        "new_visits",
        "percent_new_users",
        "bounce_rate",
        "pv_per_visit",
        "avg_tos",
        "returning_users",
        "unique_users",
        "new_users",
        "bounced_visits",
        "total_seconds",
        "non_bounced_visits",
        "local_avg_etfm_cost_per_visit",
        "local_avg_etfm_cost_per_new_visitor",
        "local_avg_etfm_cost_per_pageview",
        "local_avg_etfm_cost_per_non_bounced_visit",
        "local_avg_etfm_cost_per_minute",
        "local_avg_etfm_cost_per_unique_user",
        "video_start",
        "video_first_quartile",
        "video_midpoint",
        "video_third_quartile",
        "video_complete",
        "video_start_percent",
        "video_first_quartile_percent",
        "video_midpoint_percent",
        "video_third_quartile_percent",
        "video_complete_percent",
        "local_video_etfm_cpv",
        "local_video_etfm_cpcv",
        "mrc50_measurable",
        "mrc50_viewable",
        "mrc50_measurable_percent",
        "mrc50_viewable_percent",
        "local_etfm_mrc50_vcpm",
    ]

    m = redshiftapi.models.MVMaster()
    sql = backtosql.generate_sql(
        "rules.sql",
        {
            "breakdown": m.select_columns(subset=target_type_columns + breakdown_columns),
            "aggregates": m.select_columns(subset=aggregate_columns),
            "target_type_table": redshiftapi.view_selector.get_best_view_base(
                [
                    ttc.replace("publisher", "publisher_id").replace("placement", "placement_id")
                    for ttc in target_type_columns
                ]
                + breakdown_columns,
                "publisher" in target_type_columns,
            ),
            "ad_group_ids": "{}".format(", ".join(str(ag.id) for ag in ad_groups)),
            "last_day_key": automation.rules.constants.MetricWindow.LAST_DAY,
            "last_3_days_key": automation.rules.constants.MetricWindow.LAST_3_DAYS,
            "last_7_days_key": automation.rules.constants.MetricWindow.LAST_7_DAYS,
            "last_30_days_key": automation.rules.constants.MetricWindow.LAST_30_DAYS,
            "last_60_days_key": automation.rules.constants.MetricWindow.LAST_60_DAYS,
            "last_day_date_from": local_today - datetime.timedelta(days=1),
            "last_3_days_date_from": local_today - datetime.timedelta(days=3),
            "last_7_days_date_from": local_today - datetime.timedelta(days=7),
            "last_30_days_date_from": local_today - datetime.timedelta(days=30),
            "last_60_days_date_from": local_today - datetime.timedelta(days=60),
            "date_to": local_today - datetime.timedelta(days=1),
            "target_type_group_columns": "{}".format(", ".join(ttc for ttc in target_type_columns)),
            "limitations": _get_query_limitations(target_type),
        },
    )

    return sql


def query_conversions(target_type: int, ad_groups: Sequence[core.models.AdGroup]) -> Sequence[Any]:
    if not ad_groups:
        return []

    sql = _get_touchpoints_sql(target_type, ad_groups)
    rows = redshiftapi.db.execute_query(sql, [], _get_target_type_query_name(target_type) + ".")

    return rows


def _get_touchpoints_sql(target_type: int, ad_groups: Sequence[core.models.AdGroup]) -> str:
    local_today = utils.dates_helper.local_today()

    target_type_columns = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    breakdown_columns = ["ad_group_id", "slug", "window"]
    aggregate_columns = ["count", "count_view", "conversion_value", "conversion_value_view"]

    m = redshiftapi.models.MVTouchpointConversions()
    sql = backtosql.generate_sql(
        "rules.sql",
        {
            "breakdown": m.select_columns(subset=target_type_columns + breakdown_columns),
            "aggregates": m.select_columns(subset=aggregate_columns),
            "target_type_table": redshiftapi.view_selector.get_best_view_touchpoints(
                [
                    ttc.replace("publisher", "publisher_id").replace("placement", "placement_id")
                    for ttc in target_type_columns
                ]
                + breakdown_columns
            ),
            "ad_group_ids": "{}".format(", ".join(str(ag.id) for ag in ad_groups)),
            "last_day_key": automation.rules.constants.MetricWindow.LAST_DAY,
            "last_3_days_key": automation.rules.constants.MetricWindow.LAST_3_DAYS,
            "last_7_days_key": automation.rules.constants.MetricWindow.LAST_7_DAYS,
            "last_30_days_key": automation.rules.constants.MetricWindow.LAST_30_DAYS,
            "last_60_days_key": automation.rules.constants.MetricWindow.LAST_60_DAYS,
            "last_day_date_from": local_today - datetime.timedelta(days=1),
            "last_3_days_date_from": local_today - datetime.timedelta(days=3),
            "last_7_days_date_from": local_today - datetime.timedelta(days=7),
            "last_30_days_date_from": local_today - datetime.timedelta(days=30),
            "last_60_days_date_from": local_today - datetime.timedelta(days=60),
            "date_to": local_today - datetime.timedelta(days=1),
            "target_type_group_columns": "{}".format(
                ", ".join(ttc for ttc in ["slug", "window"] + target_type_columns)
            ),
            "limitations": _get_query_limitations(target_type),
        },
    )

    return sql


def _get_target_type_query_name(target_type: int) -> str:
    return "rule_stats__" + automation.rules.constants.TargetType.get_name(target_type).lower()


def _get_query_limitations(target_type: int):
    if target_type not in QUERY_LIMITATION_TARGET_TYPES:
        return {}
    m = redshiftapi.models.MVMaster()
    target_type_columns = automation.rules.constants.TARGET_TYPE_STATS_MAPPING[target_type]
    query_limitations = {
        "breakdown": m.select_columns(subset=target_type_columns + ["ad_group_id"]),
        "column": m.select_columns([QUERY_LIMITATION_COLUMN])[0],
        "threshold": QUERY_LIMITATION_THRESHOLD,
        "table": redshiftapi.view_selector.get_best_view_base(
            [
                ttc.replace("publisher", "publisher_id").replace("placement", "placement_id")
                for ttc in target_type_columns + ["ad_group_id"]
            ],
            "publisher" in target_type_columns,
        ),
        "target_type_group_columns": "{}".format(", ".join(ttc for ttc in target_type_columns)),
    }
    return query_limitations
