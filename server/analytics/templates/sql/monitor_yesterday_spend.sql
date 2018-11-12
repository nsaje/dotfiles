SELECT  ad_group_id, source_id,
        coalesce(sum(clicks), 0) AS total_clicks,
        ROUND(coalesce(sum(local_effective_cost_nano)::decimal/1e9, 0) +
        coalesce(sum(local_effective_data_cost_nano)::decimal/1e9, 0) +
        coalesce(sum(local_license_fee_nano)::decimal/1e9, 0) +
        coalesce(sum(local_margin_nano)::decimal/1e9, 0), 4) AS total_spend,
        ROUND(coalesce(total_spend / total_clicks, 0), 4) AS ecpc
FROM mv_adgroup
WHERE date = '{{ yesterday }}'
AND account_id NOT IN {{ excluded_account_ids }}
GROUP BY ad_group_id, source_id
HAVING SUM(impressions) > 0
AND total_spend > {{ yesterday_spend_threshold }}
AND total_clicks > 0
