SELECT *
FROM
     (
        SELECT  ad_group_id, source_id,
                coalesce(sum(clicks), 0) AS total_clicks,
                ROUND(coalesce(sum(effective_cost_nano)::decimal/1e9, 0) +
                coalesce(sum(effective_data_cost_nano)::decimal/1e9, 0) +
                coalesce(sum(service_fee_nano)::decimal/1e9, 0) +
                coalesce(sum(license_fee_nano)::decimal/1e9, 0) +
                coalesce(sum(margin_nano)::decimal/1e9, 0), 2) AS total_spend,
                ROUND(coalesce(total_spend / total_clicks, 0), 3) AS ecpc
        FROM mv_adgroup
        WHERE date = '{{ yesterday }}'
        AND account_id NOT IN {{ excluded_account_ids }}
        AND ad_group_id NOT IN {{ per_ad_groups }}
        AND source_id NOT IN {{ excluded_sources }}
        GROUP BY 1, 2
        HAVING SUM(impressions) > 0
        AND total_clicks > 0
        UNION
        SELECT  ad_group_id, 0 AS source_id,
                coalesce(sum(clicks), 0) AS total_clicks,
                ROUND(coalesce(sum(effective_cost_nano)::decimal/1e9, 0) +
                coalesce(sum(effective_data_cost_nano)::decimal/1e9, 0) +
                coalesce(sum(service_fee_nano)::decimal/1e9, 0) +
                coalesce(sum(license_fee_nano)::decimal/1e9, 0) +
                coalesce(sum(margin_nano)::decimal/1e9, 0), 4) AS total_spend,
                ROUND(coalesce(total_spend / total_clicks, 0), 3) AS ecpc
        FROM mv_adgroup
        WHERE date = '{{ yesterday }}'
        AND account_id NOT IN {{ excluded_account_ids }}
        AND ad_group_id IN {{ per_ad_groups }}
        AND source_id NOT IN {{ excluded_sources }}
        GROUP BY 1, 2
        HAVING SUM(impressions) > 0
        AND total_clicks > 0
) yesterday_spend
WHERE total_spend > {{ yesterday_spend_threshold }}
