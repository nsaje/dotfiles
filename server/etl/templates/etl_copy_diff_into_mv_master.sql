{% autoescape off %}
-- etl_insert_mv_master_stats.sql includes some similar logics that need to be updated in case this one
-- gets updated.

INSERT INTO mv_master (
  SELECT
      a.date,
      a.source_id,

      c.account_id,
      c.campaign_id,
      a.ad_group_id,
      a.content_ad_id,
      a.publisher,
      a.publisher || '__' || a.source_id as publisher_source_id,

      a.device_type,
      NULL AS device_os,
      NULL AS device_os_version,
      NULL AS placement_medium,

      NULL AS placement_type,
      NULL AS video_playback_method,

      a.country,
      a.state,
      a.dma,
      NULL AS city_id,

      a.age,
      a.gender,
      a.age_gender,

      a.impressions,
      a.clicks,
      a.cost_nano,
      a.data_cost_nano,

      a.visits,
      a.new_visits,
      a.bounced_visits,
      a.pageviews,
      a.total_time_on_site,

      round(a.cost_nano * cf.pct_actual_spend::decimal(10, 8)) as effective_cost_nano,
      round(a.data_cost_nano * cf.pct_actual_spend::decimal(10, 8)) as effective_data_cost_nano,
      round(
          (
              (nvl(a.cost_nano, 0) * cf.pct_actual_spend::decimal(10, 8)) +
              (nvl(a.data_cost_nano, 0) * cf.pct_actual_spend::decimal(10, 8))
          ) * pct_license_fee::decimal(10, 8)
      ) as license_fee_nano,
      round(
          (
              (nvl(a.cost_nano, 0) * cf.pct_actual_spend::decimal(10, 8)) +
              (nvl(a.data_cost_nano, 0) * cf.pct_actual_spend::decimal(10, 8)) +
              (
                  (nvl(a.cost_nano, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                  (nvl(a.data_cost_nano, 0) * cf.pct_actual_spend::decimal(10, 8))
              ) * cf.pct_license_fee::decimal(10, 8)
          ) * cf.pct_margin::decimal(10, 8)
      ) as margin_nano,

      a.users,
      a.returning_users,

      NULL AS video_start,
      NULL AS video_first_quartile,
      NULL AS video_midpoint,
      NULL AS video_third_quartile,
      NULL AS video_complete,
      NULL AS video_progress_3s
  FROM
    (
      mv_master_diff a
      join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id
    )
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
  WHERE
    a.date=%(date)s
    {% if account_id %}
        AND c.account_id = %(account_id)s
    {% endif %}
);

{% endautoescape %}
