INSERT INTO mv_pubs_master(
  SELECT
      COALESCE(a.date, b.date) as date,
      {{ source_id }} as source_id,

      c.agency_id as agency_id,
      c.account_id as account_id,
      c.campaign_id as campaign_id,
      c.ad_group_id as ad_group_id,
      COALESCE(a.publisher_name, b.publisher) as publisher,
      a.publisher_id as external_id,

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

      SUM(b.visits) as visits,
      SUM(b.new_visits) as new_visits,
      SUM(b.bounced_visits) as bounced_visits,
      SUM(b.pageviews) as pageviews,
      SUM(b.total_time_on_site) as total_time_on_site,

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

      SUM(b.users) as users,
      SUM(b.users - b.new_visits) as returning_users
  FROM
    (
      SELECT date, ad_group_id, publisher_id, publisher_name, SUM(clicks) as clicks FROM outbrainpublisherstats
      WHERE date BETWEEN %(date_from)s AND %(date_to)s GROUP BY 1, 2, 3, 4
    ) as a
    left outer join mvh_ad_group_cost_per_click ad_cpc on a.ad_group_id=ad_cpc.ad_group_id and a.date=ad_cpc.date
    full outer join (
      SELECT * FROM postclickstats
      WHERE source='outbrain' AND date BETWEEN %(date_from)s AND %(date_to)s
    ) as b on a.publisher_name=b.publisher and a.date=b.date and a.ad_group_id=b.ad_group_id
    join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id or b.ad_group_id=c.ad_group_id
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and (a.date=cf.date or b.date=cf.date)
  WHERE
    COALESCE(a.date, b.date) BETWEEN %(date_from)s AND %(date_to)s
    AND COALESCE(a.publisher_name, b.publisher, '') <> ''
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, clicks, cost_nano, effective_cost_nano, effective_data_cost_nano, license_fee_nano, margin_nano
)
