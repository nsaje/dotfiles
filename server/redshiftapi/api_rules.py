import datetime
from typing import Sequence

import automation.rules.constants
import backtosql
import core.models
import redshiftapi.db
import redshiftapi.models
import redshiftapi.view_selector
import utils.converters
import utils.dates_helper
import utils.dict_helper


def query(target: int, ad_groups: Sequence[core.models.AdGroup]):
    if not ad_groups:
        return []

    sql = _get_target_sql(target, ad_groups)
    rows = redshiftapi.db.execute_query(sql, [], _get_target_query_name(target))

    return rows


def _get_target_sql(target: int, ad_groups: Sequence[core.models.AdGroup]) -> str:
    local_today = utils.dates_helper.local_today()

    target_columns = automation.rules.constants.TARGET_MV_COLUMNS_MAPPING[target]
    breakdown_columns = ["ad_group_id"]
    aggregate_columns = [
        "clicks",
        "impressions",
        "etfm_cost",
        "local_etfm_cost",
        "ctr",
        "etfm_cpc",
        "local_etfm_cpc",
        "etfm_cpm",
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
        "total_pageviews",
    ]

    m = redshiftapi.models.MVMaster()
    sql = backtosql.generate_sql(
        "rules.sql",
        {
            "breakdown": m.select_columns(subset=target_columns + breakdown_columns),
            "aggregates": m.select_columns(subset=aggregate_columns),
            "target_table": redshiftapi.view_selector.get_best_view_base(
                target_columns[:1] + breakdown_columns, "publisher_id" in target_columns
            ),
            "ad_group_ids": "({})".format(", ".join(str(ag.id) for ag in ad_groups)),
            "last_day_key": automation.rules.constants.MetricWindow.LAST_DAY,
            "last_3_days_key": automation.rules.constants.MetricWindow.LAST_3_DAYS,
            "last_7_days_key": automation.rules.constants.MetricWindow.LAST_7_DAYS,
            "last_30_days_key": automation.rules.constants.MetricWindow.LAST_30_DAYS,
            "lifetime_key": automation.rules.constants.MetricWindow.LIFETIME,
            "last_day_date_from": local_today - datetime.timedelta(days=1),
            "last_3_days_date_from": local_today - datetime.timedelta(days=3),
            "last_7_days_date_from": local_today - datetime.timedelta(days=7),
            "last_30_days_date_from": local_today - datetime.timedelta(days=30),
            "lifetime_date_from": local_today - datetime.timedelta(days=60),
            "target_group_column": target_columns[0],
        },
    )

    return sql


def _get_target_query_name(target: int) -> str:
    return "rule_stats__" + automation.rules.constants.TargetType.get_name(target).lower()
