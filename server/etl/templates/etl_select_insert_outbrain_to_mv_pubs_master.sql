{% load backtosql_tags %}
{% autoescape off %}

INSERT INTO mv_pubs_master(
  SELECT
      d.date as date,
      {{ source_id }} as source_id,

      c.agency_id as agency_id,
      c.account_id as account_id,
      c.campaign_id as campaign_id,
      c.ad_group_id as ad_group_id,
      d.publisher as publisher,
      d.publisher_id as external_id,

      null as device_type,
      null as country,
      null as state,
      null as dma,
      null as age,
      null as gender,
      null as age_gender,

      d.impressions as impressions,
      d.clicks as clicks,
      d.spend * 1000 as cost_nano,
      0 as data_cost_nano,

      SUM(d.visits) as visits,
      SUM(d.new_visits) as new_visits,
      SUM(d.bounced_visits) as bounced_visits,
      SUM(d.pageviews) as pageviews,
      SUM(d.total_time_on_site) as total_time_on_site,

      round(
            d.spend * cf.pct_actual_spend::decimal(10, 8)
          * 1000
      ) as effective_cost_nano,
      0 as effective_data_cost_nano,
      round(
          (
             (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8))
          ) * cf.pct_license_fee::decimal(10, 8) * 1000
      ) as license_fee_nano,
      round(
          (
             (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_license_fee::decimal(10, 8))
          ) * cf.pct_margin::decimal(10, 8) * 1000
      ) as margin_nano,

      SUM(d.users) as users,
      SUM(d.users - d.new_visits) as returning_users
  FROM
    (
      (
        SELECT date, ad_group_id, publisher_id, publisher_name as publisher, SUM(clicks) as clicks, SUM(impressions) as impressions, SUM(spend) as spend FROM outbrainpublisherstats
        WHERE date BETWEEN %(date_from)s AND %(date_to)s
              {% if account_id %}
                  AND ad_group_id=ANY(%(ad_group_id)s)
              {% endif %}
        GROUP BY 1, 2, 3, 4
      ) a
      natural full outer join (
        SELECT * FROM postclickstats
        WHERE source='outbrain' AND date BETWEEN %(date_from)s AND %(date_to)s
              {% if account_id %}
                  AND ad_group_id=ANY(%(ad_group_id)s)
              {% endif %}
      ) b
      natural full outer join (
        SELECT date, source_id, ad_group_id, publisher FROM mv_touchpointconversions
        WHERE source_id={{ source_id }} AND date BETWEEN %(date_from)s AND %(date_to)s
          {% if account_id %}
            AND ad_group_id=ANY(%(ad_group_id)s)
          {% endif %}
        GROUP BY 1, 2, 3, 4
      ) tpc
    ) d
    join mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
    join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
  WHERE
    d.date BETWEEN %(date_from)s AND %(date_to)s
    AND COALESCE(d.publisher, '') <> ''
    {% if account_id %}
      AND d.ad_group_id=ANY(%(ad_group_id)s)
    {% endif %}

  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, impressions, clicks, cost_nano, effective_cost_nano, effective_data_cost_nano, license_fee_nano, margin_nano
)

{% endautoescape %}
