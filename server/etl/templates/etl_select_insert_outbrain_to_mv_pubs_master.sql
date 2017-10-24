{% load backtosql_tags %}
{% autoescape off %}

INSERT INTO mv_master_pubs(
SELECT
    d.date,
    {{ source_id }} as source_id,

    c.account_id,
    c.campaign_id,
    c.ad_group_id,
    d.publisher,  -- publisher should not be null
    d.publisher || '__{{ source_id }}' AS publisher_source_id,
    d.publisher_id as external_id,

    NULL AS device_type,
    NULL AS device_os,
    NULL AS device_os_version,
    NULL AS placement_medium,

    NULL AS placement_type,
    NULL AS video_playback_method,

    NULL AS country,
    NULL AS state,
    NULL AS dma,
    NULL AS city_id,

    NULL AS age,
    NULL AS gender,
    NULL AS age_gender,

    d.impressions,
    d.clicks,
    d.spend * 1000 as cost_nano,
    0 as data_cost_nano,

    d.visits,
    d.new_visits,
    d.bounced_visits,
    d.pageviews,
    d.total_time_on_site,

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

    d.users,
    d.users - d.new_visits as returning_users,

    NULL as video_start,
    NULL as video_first_quartile,
    NULL as video_midpoint,
    NULL as video_third_quartile,
    NULL as video_complete,
    NULL as video_progress_3s
FROM
  (
    (
      SELECT date, ad_group_id, publisher_id, publisher_name as publisher, SUM(clicks) as clicks, SUM(impressions) as impressions, SUM(spend) as spend
      FROM outbrainpublisherstats
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

)
{% endautoescape %}
