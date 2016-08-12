INSERT INTO mv_pubs_master(
  SELECT
      a.date as date,
      {{ source_id }} as source_id,

      c.agency_id as agency_id,
      c.account_id as account_id,
      c.campaign_id as campaign_id,
      a.ad_group_id as ad_group_id,
      a.publisher_name as publisher,

      null as device_type,
      null as country,
      null as state,
      null as dma,
      null as age,
      null as gender,
      null as age_gender,

      0 as impressions,
      a.clicks as clicks,
      a.clicks::bigint * ad_cpc.cpc * 1000 as cost_nano,
      0 as data_cost_nano,

      null as visits,
      null as new_visits,
      null as bounced_visits,
      null as pageviews,
      null as total_time_on_site,

      round(
            a.clicks * ad_cpc.cpc * cf.pct_actual_spend::decimal(10, 8)
          * 1000
      ) as effective_cost_nano,
      0 as effective_data_cost_nano,
      round(
          (
             (nvl(a.clicks, 0) * ad_cpc.cpc * cf.pct_actual_spend::decimal(10, 8))
          ) * cf.pct_license_fee::decimal(10, 8) * 1000
      ) as license_fee_nano,
      round(
          (
             (nvl(a.clicks, 0) * ad_cpc.cpc * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_license_fee::decimal(10, 8))
          ) * cf.pct_margin::decimal(10, 8) * 1000
      ) as margin_nano,

      null as users,
      null as returning_users
  FROM
    (
      outbrainpublisherstats a
      join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id
    )
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
    left outer join mvh_ad_group_cost_per_click ad_cpc on a.ad_group_id=ad_cpc.ad_group_id and a.date=ad_cpc.date
  WHERE
  a.date BETWEEN %(date_from)s AND %(date_to)s
)