{% autoescape off %}
-- etl_insert_mv_master_stats.sql includes some similar logics that need to be updated in case this one
-- gets updated.

INSERT INTO mv_master (
  SELECT
      a.date as date,
      a.source_id as source_id,

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
      ) as license_fee_nano
  FROM
    (
      mv_master_diff a
      join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id
    )
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
  WHERE
    a.date=%(date)s
);

{% endautoescape %}