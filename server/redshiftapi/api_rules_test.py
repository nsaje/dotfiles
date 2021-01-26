import datetime

import mock
from django.test import TestCase

import automation.rules.constants
import core.models
from utils.magic_mixer import magic_mixer

from . import api_rules


@mock.patch("utils.dates_helper.local_today", return_value=datetime.date(2017, 7, 7))
class ApiRulesTest(TestCase):
    def test_get_target_type_sql(self, mock_today):
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        ad_group_ids = [ag.id for ag in ad_groups]

        test_cases = [
            {
                "target_type": automation.rules.constants.TargetType.AD_GROUP,
                "table": "mv_adgroup",
                "fields": "ad_group_id AS ad_group_id",
            },
            {
                "target_type": automation.rules.constants.TargetType.AD,
                "table": "mv_contentad",
                "fields": "content_ad_id AS content_ad_id",
            },
            {
                "target_type": automation.rules.constants.TargetType.PUBLISHER,
                "table": "mv_adgroup_pubs",
                "fields": "publisher AS publisher, source_id AS source_id",
            },
            {
                "target_type": automation.rules.constants.TargetType.PLACEMENT,
                "table": "mv_adgroup_placement",
                "fields": "publisher AS publisher, source_id AS source_id, placement AS placement",
            },
            {
                "target_type": automation.rules.constants.TargetType.DEVICE,
                "table": "mv_adgroup_device",
                "fields": "device_type AS device_type",
            },
            {
                "target_type": automation.rules.constants.TargetType.COUNTRY,
                "table": "mv_adgroup_geo",
                "fields": "country AS country",
            },
            {
                "target_type": automation.rules.constants.TargetType.STATE,
                "table": "mv_adgroup_geo",
                "fields": "state AS region",
            },
            {
                "target_type": automation.rules.constants.TargetType.DMA,
                "table": "mv_adgroup_geo",
                "fields": "dma AS dma",
            },
            {
                "target_type": automation.rules.constants.TargetType.OS,
                "table": "mv_adgroup_device",
                "fields": "device_os AS device_os",
            },
            {
                "target_type": automation.rules.constants.TargetType.ENVIRONMENT,
                "table": "mv_adgroup_environment",
                "fields": "environment AS environment",
            },
            {
                "target_type": automation.rules.constants.TargetType.SOURCE,
                "table": "mv_adgroup",
                "fields": "source_id AS source_id",
            },
            {
                "target_type": automation.rules.constants.TargetType.BROWSER,
                "table": "mv_adgroup_device",
                "fields": "browser AS browser",
            },
            {
                "target_type": automation.rules.constants.TargetType.CONNECTION_TYPE,
                "table": "mv_adgroup_device",
                "fields": "connection_type AS connection_type",
            },
        ]

        for test_case in test_cases:
            target_type_sql = api_rules._get_target_type_sql(test_case["target_type"], ad_groups)

            expected_sql = ""
            if test_case["target_type"] in api_rules.QUERY_LIMITATION_TARGET_TYPES:
                expected_sql = """\
WITH limited_entities AS (
    SELECT
        {fields}, ad_group_id AS ad_group_id,
        SUM(impressions) / NULLIF(SUM(CASE WHEN impressions > 0 THEN 1 ELSE 0 END), 0) per_day
        FROM (
            SELECT
                {fields}, ad_group_id AS ad_group_id,
                date,
                SUM(impressions) impressions
            FROM
                {table}
            WHERE
                ad_group_id IN {ad_group_ids}
                AND date >= '2017-05-08'
            GROUP BY
                ad_group_id,
                {group_by},
                date)
        GROUP BY
            ad_group_id,
            {group_by}
        HAVING
            per_day > {limit_min_threshold})
"""

            expected_sql += """\
(
    SELECT
        1 as window_key,
        {fields}, ad_group_id AS ad_group_id,
        SUM(clicks) clicks, SUM(impressions) impressions, (COALESCE(SUM(local_effective_cost_nano), 0) +
 COALESCE(SUM(local_effective_data_cost_nano), 0) +
 COALESCE(SUM(local_license_fee_nano), 0) +
 COALESCE(SUM(local_margin_nano), 0)
)::float/1000000000 local_etfm_cost, SUM(clicks)::FLOAT / (
NULLIF(SUM(impressions), 0) * 0.01)
ctr, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(clicks), 0) * 1000000000)
local_etfm_cpc, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(impressions), 0) * 1000000.0)
local_etfm_cpm, SUM(visits) visits, SUM(pageviews) pageviews, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks)
END)*100.0 click_discrepancy, SUM(new_visits) new_visits, SUM(new_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
percent_new_users, SUM(bounced_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
bounce_rate, SUM(pageviews)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
pv_per_visit, SUM(total_time_on_site)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
avg_tos, SUM(returning_users) returning_users, SUM(users) unique_users, SUM(new_visits) new_users, SUM(bounced_visits) bounced_visits, SUM(total_time_on_site) total_seconds, (COALESCE(SUM(visits)) - COALESCE(SUM(bounced_visits), 0)) non_bounced_visits, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(visits), 0) * 1000000000)
local_avg_etfm_cost_per_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(new_visits), 0) * 1000000000)
local_avg_etfm_cost_per_new_visitor, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(pageviews), 0) * 1000000000)
local_avg_etfm_cost_per_pageview, ( COALESCE( SUM(local_effective_cost_nano), 0 ) +
  COALESCE( SUM(local_effective_data_cost_nano), 0 ) +
  COALESCE( SUM(local_license_fee_nano), 0 ) +
  COALESCE( SUM(local_margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( visits ), 0 ) -
     COALESCE( SUM( bounced_visits ), 0 )
  ) * 1000000000, 0 )
local_avg_etfm_cost_per_non_bounced_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(total_time_on_site), 0) * 16666666.666666666)
local_avg_etfm_cost_per_minute, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(users), 0) * 1000000000)
local_avg_etfm_cost_per_unique_user, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_first_quartile), 0) * 1000000000)
local_video_etfm_cpv, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_complete), 0) * 1000000000)
local_video_etfm_cpcv
    FROM
        {table}{limit_join}
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-07-06'
        AND date <= '2017-07-06'
    GROUP BY
        ad_group_id,
        {group_by}
) UNION ALL (
    SELECT
        2 as window_key,
        {fields}, ad_group_id AS ad_group_id,
        SUM(clicks) clicks, SUM(impressions) impressions, (COALESCE(SUM(local_effective_cost_nano), 0) +
 COALESCE(SUM(local_effective_data_cost_nano), 0) +
 COALESCE(SUM(local_license_fee_nano), 0) +
 COALESCE(SUM(local_margin_nano), 0)
)::float/1000000000 local_etfm_cost, SUM(clicks)::FLOAT / (
NULLIF(SUM(impressions), 0) * 0.01)
ctr, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(clicks), 0) * 1000000000)
local_etfm_cpc, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(impressions), 0) * 1000000.0)
local_etfm_cpm, SUM(visits) visits, SUM(pageviews) pageviews, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks)
END)*100.0 click_discrepancy, SUM(new_visits) new_visits, SUM(new_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
percent_new_users, SUM(bounced_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
bounce_rate, SUM(pageviews)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
pv_per_visit, SUM(total_time_on_site)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
avg_tos, SUM(returning_users) returning_users, SUM(users) unique_users, SUM(new_visits) new_users, SUM(bounced_visits) bounced_visits, SUM(total_time_on_site) total_seconds, (COALESCE(SUM(visits)) - COALESCE(SUM(bounced_visits), 0)) non_bounced_visits, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(visits), 0) * 1000000000)
local_avg_etfm_cost_per_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(new_visits), 0) * 1000000000)
local_avg_etfm_cost_per_new_visitor, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(pageviews), 0) * 1000000000)
local_avg_etfm_cost_per_pageview, ( COALESCE( SUM(local_effective_cost_nano), 0 ) +
  COALESCE( SUM(local_effective_data_cost_nano), 0 ) +
  COALESCE( SUM(local_license_fee_nano), 0 ) +
  COALESCE( SUM(local_margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( visits ), 0 ) -
     COALESCE( SUM( bounced_visits ), 0 )
  ) * 1000000000, 0 )
local_avg_etfm_cost_per_non_bounced_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(total_time_on_site), 0) * 16666666.666666666)
local_avg_etfm_cost_per_minute, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(users), 0) * 1000000000)
local_avg_etfm_cost_per_unique_user, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_first_quartile), 0) * 1000000000)
local_video_etfm_cpv, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_complete), 0) * 1000000000)
local_video_etfm_cpcv
    FROM
        {table}{limit_join}
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-07-04'
        AND date <= '2017-07-06'
    GROUP BY
        ad_group_id,
        {group_by}
) UNION ALL (
    SELECT
        3 as window_key,
        {fields}, ad_group_id AS ad_group_id,
        SUM(clicks) clicks, SUM(impressions) impressions, (COALESCE(SUM(local_effective_cost_nano), 0) +
 COALESCE(SUM(local_effective_data_cost_nano), 0) +
 COALESCE(SUM(local_license_fee_nano), 0) +
 COALESCE(SUM(local_margin_nano), 0)
)::float/1000000000 local_etfm_cost, SUM(clicks)::FLOAT / (
NULLIF(SUM(impressions), 0) * 0.01)
ctr, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(clicks), 0) * 1000000000)
local_etfm_cpc, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(impressions), 0) * 1000000.0)
local_etfm_cpm, SUM(visits) visits, SUM(pageviews) pageviews, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks)
END)*100.0 click_discrepancy, SUM(new_visits) new_visits, SUM(new_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
percent_new_users, SUM(bounced_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
bounce_rate, SUM(pageviews)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
pv_per_visit, SUM(total_time_on_site)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
avg_tos, SUM(returning_users) returning_users, SUM(users) unique_users, SUM(new_visits) new_users, SUM(bounced_visits) bounced_visits, SUM(total_time_on_site) total_seconds, (COALESCE(SUM(visits)) - COALESCE(SUM(bounced_visits), 0)) non_bounced_visits, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(visits), 0) * 1000000000)
local_avg_etfm_cost_per_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(new_visits), 0) * 1000000000)
local_avg_etfm_cost_per_new_visitor, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(pageviews), 0) * 1000000000)
local_avg_etfm_cost_per_pageview, ( COALESCE( SUM(local_effective_cost_nano), 0 ) +
  COALESCE( SUM(local_effective_data_cost_nano), 0 ) +
  COALESCE( SUM(local_license_fee_nano), 0 ) +
  COALESCE( SUM(local_margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( visits ), 0 ) -
     COALESCE( SUM( bounced_visits ), 0 )
  ) * 1000000000, 0 )
local_avg_etfm_cost_per_non_bounced_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(total_time_on_site), 0) * 16666666.666666666)
local_avg_etfm_cost_per_minute, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(users), 0) * 1000000000)
local_avg_etfm_cost_per_unique_user, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_first_quartile), 0) * 1000000000)
local_video_etfm_cpv, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_complete), 0) * 1000000000)
local_video_etfm_cpcv
    FROM
        {table}{limit_join}
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-06-30'
        AND date <= '2017-07-06'
    GROUP BY
        ad_group_id,
        {group_by}
) UNION ALL (
    SELECT
        4 as window_key,
        {fields}, ad_group_id AS ad_group_id,
        SUM(clicks) clicks, SUM(impressions) impressions, (COALESCE(SUM(local_effective_cost_nano), 0) +
 COALESCE(SUM(local_effective_data_cost_nano), 0) +
 COALESCE(SUM(local_license_fee_nano), 0) +
 COALESCE(SUM(local_margin_nano), 0)
)::float/1000000000 local_etfm_cost, SUM(clicks)::FLOAT / (
NULLIF(SUM(impressions), 0) * 0.01)
ctr, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(clicks), 0) * 1000000000)
local_etfm_cpc, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(impressions), 0) * 1000000.0)
local_etfm_cpm, SUM(visits) visits, SUM(pageviews) pageviews, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks)
END)*100.0 click_discrepancy, SUM(new_visits) new_visits, SUM(new_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
percent_new_users, SUM(bounced_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
bounce_rate, SUM(pageviews)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
pv_per_visit, SUM(total_time_on_site)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
avg_tos, SUM(returning_users) returning_users, SUM(users) unique_users, SUM(new_visits) new_users, SUM(bounced_visits) bounced_visits, SUM(total_time_on_site) total_seconds, (COALESCE(SUM(visits)) - COALESCE(SUM(bounced_visits), 0)) non_bounced_visits, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(visits), 0) * 1000000000)
local_avg_etfm_cost_per_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(new_visits), 0) * 1000000000)
local_avg_etfm_cost_per_new_visitor, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(pageviews), 0) * 1000000000)
local_avg_etfm_cost_per_pageview, ( COALESCE( SUM(local_effective_cost_nano), 0 ) +
  COALESCE( SUM(local_effective_data_cost_nano), 0 ) +
  COALESCE( SUM(local_license_fee_nano), 0 ) +
  COALESCE( SUM(local_margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( visits ), 0 ) -
     COALESCE( SUM( bounced_visits ), 0 )
  ) * 1000000000, 0 )
local_avg_etfm_cost_per_non_bounced_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(total_time_on_site), 0) * 16666666.666666666)
local_avg_etfm_cost_per_minute, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(users), 0) * 1000000000)
local_avg_etfm_cost_per_unique_user, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_first_quartile), 0) * 1000000000)
local_video_etfm_cpv, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_complete), 0) * 1000000000)
local_video_etfm_cpcv
    FROM
        {table}{limit_join}
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-06-07'
        AND date <= '2017-07-06'
    GROUP BY
        ad_group_id,
        {group_by}
) UNION ALL (
    SELECT
        5 as window_key,
        {fields}, ad_group_id AS ad_group_id,
        SUM(clicks) clicks, SUM(impressions) impressions, (COALESCE(SUM(local_effective_cost_nano), 0) +
 COALESCE(SUM(local_effective_data_cost_nano), 0) +
 COALESCE(SUM(local_license_fee_nano), 0) +
 COALESCE(SUM(local_margin_nano), 0)
)::float/1000000000 local_etfm_cost, SUM(clicks)::FLOAT / (
NULLIF(SUM(impressions), 0) * 0.01)
ctr, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(clicks), 0) * 1000000000)
local_etfm_cpc, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(impressions), 0) * 1000000.0)
local_etfm_cpm, SUM(visits) visits, SUM(pageviews) pageviews, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks)
END)*100.0 click_discrepancy, SUM(new_visits) new_visits, SUM(new_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
percent_new_users, SUM(bounced_visits)::FLOAT / (
NULLIF(SUM(visits), 0) * 0.01)
bounce_rate, SUM(pageviews)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
pv_per_visit, SUM(total_time_on_site)::FLOAT / (
NULLIF(SUM(visits), 0) * 1)
avg_tos, SUM(returning_users) returning_users, SUM(users) unique_users, SUM(new_visits) new_users, SUM(bounced_visits) bounced_visits, SUM(total_time_on_site) total_seconds, (COALESCE(SUM(visits)) - COALESCE(SUM(bounced_visits), 0)) non_bounced_visits, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(visits), 0) * 1000000000)
local_avg_etfm_cost_per_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(new_visits), 0) * 1000000000)
local_avg_etfm_cost_per_new_visitor, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(pageviews), 0) * 1000000000)
local_avg_etfm_cost_per_pageview, ( COALESCE( SUM(local_effective_cost_nano), 0 ) +
  COALESCE( SUM(local_effective_data_cost_nano), 0 ) +
  COALESCE( SUM(local_license_fee_nano), 0 ) +
  COALESCE( SUM(local_margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( visits ), 0 ) -
     COALESCE( SUM( bounced_visits ), 0 )
  ) * 1000000000, 0 )
local_avg_etfm_cost_per_non_bounced_visit, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(total_time_on_site), 0) * 16666666.666666666)
local_avg_etfm_cost_per_minute, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(users), 0) * 1000000000)
local_avg_etfm_cost_per_unique_user, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_first_quartile), 0) * 1000000000)
local_video_etfm_cpv, (
  COALESCE(SUM(local_effective_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_effective_data_cost_nano)::FLOAT, 0) +
  COALESCE(SUM(local_license_fee_nano)::FLOAT, 0) +
  COALESCE(SUM(local_margin_nano)::FLOAT, 0)
)::FLOAT / (NULLIF(SUM(video_complete), 0) * 1000000000)
local_video_etfm_cpcv
    FROM
        {table}{limit_join}
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-05-08'
        AND date <= '2017-07-06'
    GROUP BY
        ad_group_id,
        {group_by}
)"""
            self.assertEqual(
                expected_sql.format(
                    table=test_case["table"],
                    limit_join="""
    NATURAL JOIN limited_entities"""
                    if test_case["target_type"] in api_rules.QUERY_LIMITATION_TARGET_TYPES
                    else "",
                    fields=test_case["fields"],
                    ad_group_ids=tuple(ad_group_ids),
                    limit_min_threshold=api_rules.QUERY_LIMITATION_THRESHOLD,
                    group_by=", ".join(
                        [
                            field
                            for field in automation.rules.constants.TARGET_TYPE_STATS_MAPPING[test_case["target_type"]]
                        ]
                    ),
                ),
                target_type_sql,
            )

    @mock.patch("redshiftapi.db.execute_query")
    def test_query_for_target_type(self, mock_redshift, mock_today):
        mock_redshift.return_value = [123]
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)

        test_cases = [
            {"target_type": automation.rules.constants.TargetType.AD_GROUP, "name": "ad_group"},
            {"target_type": automation.rules.constants.TargetType.AD, "name": "ad"},
            {"target_type": automation.rules.constants.TargetType.PUBLISHER, "name": "publisher"},
            {"target_type": automation.rules.constants.TargetType.DEVICE, "name": "device"},
            {"target_type": automation.rules.constants.TargetType.COUNTRY, "name": "country"},
            {"target_type": automation.rules.constants.TargetType.STATE, "name": "state"},
            {"target_type": automation.rules.constants.TargetType.DMA, "name": "dma"},
            {"target_type": automation.rules.constants.TargetType.OS, "name": "os"},
            {"target_type": automation.rules.constants.TargetType.ENVIRONMENT, "name": "environment"},
            {"target_type": automation.rules.constants.TargetType.SOURCE, "name": "source"},
            {"target_type": automation.rules.constants.TargetType.PLACEMENT, "name": "placement"},
            {"target_type": automation.rules.constants.TargetType.BROWSER, "name": "browser"},
            {"target_type": automation.rules.constants.TargetType.CONNECTION_TYPE, "name": "connection_type"},
        ]

        for test_case in test_cases:
            rows = api_rules.query(test_case["target_type"], ad_groups)
            self.assertEqual([123], rows)
            mock_redshift.assert_called_once_with(mock.ANY, [], f'rule_stats__{test_case["name"]}', db_cluster=mock.ANY)
            mock_redshift.reset_mock()
