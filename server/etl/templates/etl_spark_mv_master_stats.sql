{% autoescape off %}
-- etl_copy_diff_into_mv_master.sql includes some similar logics that need to be updated in case this one
-- gets updated.

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
  cast(d.spend AS long) * 1000 as cost_nano,
  cast(d.data_spend AS long) * 1000 as data_cost_nano,

  null as visits,
  null as new_visits,
  null as bounced_visits,
  null as pageviews,
  null as total_time_on_site,

  round(d.spend * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)) * 1000) as effective_cost_nano,
  round(d.data_spend * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)) * 1000) as effective_data_cost_nano,
  round(
      cast(
          (nvl(d.spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
          (nvl(d.data_spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)))
          AS decimal(38, 18)
      ) * cast(floor(cf.pct_license_fee * 100000000)/100000000 AS decimal(10, 8)) * 1000
  ) as license_fee_nano,
  round(
      cast(
          (nvl(d.spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
          (nvl(d.data_spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
          cast(
              (nvl(d.spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
              (nvl(d.data_spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)))
              AS decimal(38, 18)
          ) * cast(floor(cf.pct_license_fee * 100000000)/100000000 AS decimal(10, 8))
          AS decimal(38, 18)
      ) * cast(floor(cf.pct_margin * 100000000)/100000000 AS decimal(10, 8)) * 1000
  ) as margin_nano,

  null as users,
  null as returning_users,

  d.video_start as video_start,
  d.video_first_quartile as video_first_quartile,
  d.video_midpoint as video_midpoint,
  d.video_third_quartile as video_third_quartile,
  d.video_complete as video_complete,
  d.video_progress_3s as video_progress_3s,

  round(cast(d.spend AS long) * 1000 * cast(floor(cer.exchange_rate * 10000)/10000 AS decimal(10, 4))) as local_cost_nano,
  round(cast(d.data_spend AS long) * 1000 * cast(floor(cer.exchange_rate * 10000)/10000 AS decimal(10, 4))) as local_data_cost_nano,
  -- casting intermediate values to bigint (decimal(19, 0)) because of max precision of 38 in DB
  round(cast(round(d.spend * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)) * 1000) AS long) * cast(floor(cer.exchange_rate * 10000)/10000 AS decimal(10, 4))) as local_effective_cost_nano,
  round(cast(round(d.data_spend * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)) * 1000) AS long) * cast(floor(cer.exchange_rate * 10000)/10000 AS decimal(10, 4))) as local_effective_data_cost_nano,
  round(
      cast(round(
          cast(
              (nvl(d.spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
              (nvl(d.data_spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)))
              AS decimal(38, 18)
          ) * cast(floor(cf.pct_license_fee * 100000000)/100000000 AS decimal(10, 8)) * 1000
      ) AS long) * cast(floor(cer.exchange_rate * 10000)/10000 AS decimal(10, 4))
  ) as local_license_fee_nano,
  round(
      cast(round(
          cast(
              (nvl(d.spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
              (nvl(d.data_spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
              cast(
                  (nvl(d.spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8))) +
                  (nvl(d.data_spend, 0) * cast(floor(cf.pct_actual_spend * 100000000)/100000000 AS decimal(10, 8)))
                  AS decimal(38, 18)
              ) * cast(floor(cf.pct_license_fee * 100000000)/100000000 AS decimal(10, 8))
              AS decimal(38, 18)
          ) * cast(floor(cf.pct_margin * 100000000)/100000000 AS decimal(10, 8)) * 1000
      ) AS long) * cast(floor(cer.exchange_rate * 10000)/10000 AS decimal(10, 4))
  ) as local_margin_nano
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
    WHERE date BETWEEN '{{ date_from }}' AND '{{ date_to }}'
    {% if account_id %}
      AND account_id={{ account_id }}
    {% endif %}
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
  ) tpc
) d
join mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
join mvh_currency_exchange_rates cer on c.account_id=cer.account_id and d.date=cer.date
WHERE
d.date BETWEEN '{{ date_from }}' AND '{{ date_to }}'
{% if account_id %}
    AND c.account_id={{ account_id }}
{% endif %}

{% endautoescape %}
