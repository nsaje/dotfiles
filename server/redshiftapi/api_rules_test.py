import datetime

import mock
from django.test import TestCase

import automation.rules.constants
import core.models
from utils.magic_mixer import magic_mixer

from . import api_rules


@mock.patch("utils.dates_helper.local_today", return_value=datetime.date(2017, 7, 7))
class ApiRulesTest(TestCase):
    def test_get_publisher_sql(self, mock_today):
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        ad_group_ids = [ag.id for ag in ad_groups]

        self.assertEqual(
            """(
    SELECT
        2 as window_key,
        publisher AS publisher, source_id AS source_id, ad_group_id AS ad_group_id,
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
local_avg_etfm_cost_for_new_visitor, (
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
local_avg_etfm_cost_per_minute, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
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
        mv_adgroup_pubs
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-07-06'
    GROUP BY
        ad_group_id,
        publisher, source_id
) UNION ALL (
    SELECT
        3 as window_key,
        publisher AS publisher, source_id AS source_id, ad_group_id AS ad_group_id,
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
local_avg_etfm_cost_for_new_visitor, (
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
local_avg_etfm_cost_per_minute, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
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
        mv_adgroup_pubs
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-07-04'
    GROUP BY
        ad_group_id,
        publisher, source_id
) UNION ALL (
    SELECT
        4 as window_key,
        publisher AS publisher, source_id AS source_id, ad_group_id AS ad_group_id,
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
local_avg_etfm_cost_for_new_visitor, (
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
local_avg_etfm_cost_per_minute, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
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
        mv_adgroup_pubs
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-06-30'
    GROUP BY
        ad_group_id,
        publisher, source_id
) UNION ALL (
    SELECT
        5 as window_key,
        publisher AS publisher, source_id AS source_id, ad_group_id AS ad_group_id,
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
local_avg_etfm_cost_for_new_visitor, (
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
local_avg_etfm_cost_per_minute, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
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
        mv_adgroup_pubs
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-06-07'
    GROUP BY
        ad_group_id,
        publisher, source_id
) UNION ALL (
    SELECT
        6 as window_key,
        publisher AS publisher, source_id AS source_id, ad_group_id AS ad_group_id,
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
local_avg_etfm_cost_for_new_visitor, (
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
local_avg_etfm_cost_per_minute, SUM(video_start) video_start, SUM(video_first_quartile) video_first_quartile, SUM(video_midpoint) video_midpoint, SUM(video_third_quartile) video_third_quartile, SUM(video_complete) video_complete, (
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
        mv_adgroup_pubs
    WHERE
        ad_group_id IN {ad_group_ids}
        AND date >= '2017-05-08'
    GROUP BY
        ad_group_id,
        publisher, source_id
)""".format(
                ad_group_ids=tuple(ad_group_ids)
            ),
            api_rules._get_target_type_sql(automation.rules.constants.TargetType.PUBLISHER, ad_groups),
        )

    @mock.patch("redshiftapi.db.execute_query")
    def test_query_publisher(self, mock_redshift, mock_today):
        mock_redshift.return_value = [123]

        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup)
        rows = api_rules.query(automation.rules.constants.TargetType.PUBLISHER, ad_groups)

        self.assertEqual([123], rows)
        mock_redshift.assert_called_once_with(mock.ANY, [], "rule_stats__publisher")
