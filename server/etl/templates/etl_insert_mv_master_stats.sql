{% autoescape off %}
-- etl_copy_diff_into_mv_master.sql includes some similar logics that need to be updated in case this one
-- gets updated.

INSERT INTO mv_master (
  SELECT
      d.date,
      d.source_id,

      c.account_id,
      c.campaign_id,
      d.ad_group_id,
      d.content_ad_id,

      d.publisher,
      COALESCE(d.publisher, '') || '__' || d.source_id as publisher_source_id,

      -- When adding new breakdown dimensions, add them to natural full outer join with mv_touchpointconversions below
      -- too!
      d.device_type,
      d.device_os,
      d.device_os_version,
      d.placement_medium,

      d.placement_type,
      d.video_playback_method,

      d.country,
      d.state,
      d.dma,
      d.city_id,

      d.age as age,
      d.gender as gender,
      d.age_gender as age_gender,

      d.impressions as impressions,
      d.clicks as clicks,
      -- convert micro to nano
      d.spend::bigint * 1000 as cost_nano,
      d.data_spend::bigint * 1000 as data_cost_nano,

      null as visits,
      null as new_visits,
      null as bounced_visits,
      null as pageviews,
      null as total_time_on_site,

      round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_cost_nano,
      round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_data_cost_nano,
      round(
          (
              (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
              (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
          ) * cf.pct_license_fee::decimal(10, 8) * 1000
      ) as license_fee_nano,
      round(
          (
              (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
              (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
              (
                  (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                  (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
              ) * cf.pct_license_fee::decimal(10, 8)
          ) * cf.pct_margin::decimal(10, 8) * 1000
      ) as margin_nano,

      null as users,
      null as returning_users,

      d.video_start as video_start,
      d.video_first_quartile as video_first_quartile,
      d.video_midpoint as video_midpoint,
      d.video_third_quartile as video_third_quartile,
      d.video_complete as video_complete,
      d.video_progress_3s as video_progress_3s,

      null as local_cost_nano,                 -- TODO (jurebajt): Calculate using mvh_currency_exchange_rates
      null as local_data_cost_nano,            -- TODO (jurebajt): Calculate using mvh_currency_exchange_rates
      null as local_effective_cost_nano,       -- TODO (jurebajt): Calculate using mvh_currency_exchange_rates
      null as local_effective_data_cost_nano,  -- TODO (jurebajt): Calculate using mvh_currency_exchange_rates
      null as local_license_fee_nano,          -- TODO (jurebajt): Calculate using mvh_currency_exchange_rates
      null as local_margin_nano                -- TODO (jurebajt): Calculate using mvh_currency_exchange_rates
  FROM
    (
      (mvh_clean_stats a left outer join mvh_source b on a.source_slug=b.bidder_slug)
      natural full outer join (
        SELECT
          date,
          source_id,
          ad_group_id,
          content_ad_id,
          device_type,
          device_os,
          device_os_version,
          placement_medium,
          country,
          state,
          dma,
          CASE WHEN source_id = 3 THEN NULL ELSE publisher END AS publisher
        FROM mv_touchpointconversions
        WHERE date=%(date)s
        {% if account_id %}
          AND account_id=%(account_id)s
        {% endif %}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
      ) tpc
    ) d
    join mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
  WHERE
    d.date=%(date)s
    {% if account_id %}
        AND c.account_id=%(account_id)s
    {% endif %}
);

{% endautoescape %}
