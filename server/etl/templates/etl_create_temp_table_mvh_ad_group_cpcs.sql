{% autoescape off %}

CREATE TEMP TABLE mvh_ad_group_cost_per_click AS
SELECT
  date,
  ad_group_id,
  CASE WHEN SUM(clicks) <> 0 AND SUM(spend) <> 0 THEN round(SUM(spend)::decimal / SUM(clicks))
       ELSE NULL
  END as cpc
FROM stats
WHERE media_source ILIKE %(source_name)s AND date BETWEEN %(date_from)s AND %(date_to)s
GROUP BY date, ad_group_id;

{% endautoescape %}