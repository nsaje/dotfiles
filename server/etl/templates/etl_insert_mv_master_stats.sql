INSERT INTO mv_master (
  SELECT
      a.date as date,
      b.source_id as source_id,

      c.agency_id as agency_id,
      c.account_id as account_id,
      c.campaign_id as campaign_id,
      a.ad_group_id as ad_group_id,
      a.content_ad_id as content_ad_id,
      a.publisher as publisher,

      a.device_type as device_type,
      a.country as country,
      a.state as state,
      a.dma as dma,
      a.age as age,
      a.gender as gender,
      a.age_gender as age_gender,

      a.impressions as impressions,
      a.clicks as clicks,
      cast( (cast(a.spend as decimal) / 100) as integer) as cost_cc,
      cast( (cast(a.data_spend as decimal) / 100) as integer) as data_cost_cc,

      null as visits,
      null as new_visits,
      null as bounced_visits,
      null as pageviews,
      null as total_time_on_site,

      round(a.spend * cf.pct_actual_spend::decimal(10, 2) * 1000) as effective_cost_nano,
      round(a.data_spend * cf.pct_actual_spend::decimal(10, 2) * 1000) as effective_data_cost_nano,
      round(((a.spend * cf.pct_actual_spend::decimal(10, 2)) + (a.data_spend * cf.pct_actual_spend::decimal(10, 2))) * pct_license_fee::decimal(10, 2) * 1000) as license_fee_nano,

      null as conversions,
      null as tp_conversions
  FROM
    (
      (mvh_clean_stats a left outer join mvh_source b on a.source_slug=b.bidder_slug)
      join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id
    )
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
);
