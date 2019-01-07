SELECT
      breakdown.{{ key }}_id,
      breakdown.impressions,
      breakdown.clicks,
      breakdown.visits,
      breakdown.media,
      breakdown.data,
      breakdown.fee,
      breakdown.margin,
      nvl(mv_touchpointconversions.conversions,0) + nvl(mv_conversions.conversions, 0) AS conversions
FROM
    (SELECT {{ key }}_id,
    nvl(sum(impressions), 0) AS impressions,
    nvl(sum(clicks), 0) AS clicks,
    nvl(sum(visits), 0) AS visits,
    nvl(sum(effective_cost_nano::decimal), 0)/1000000000.0 AS media,
    nvl(sum(effective_data_cost_nano::decimal), 0)/1000000000.0 AS DATA,
    nvl(sum(license_fee_nano::decimal), 0)/1000000000.0 AS fee,
    nvl(sum(margin_nano::decimal), 0)/1000000000.0 AS margin
    FROM mv_adgroup
    WHERE date = '{{ date }}'
    AND {{ key }}_id IN ({{ value }})
    GROUP BY {{ key }}_id) AS breakdown
LEFT JOIN
    (SELECT {{ key }}_id,
    nvl(sum(conversion_count), 0) AS conversions
    FROM mv_conversions
    WHERE date = '{{ date }}'
    AND {{ key }}_id IN ({{ value }})
    GROUP BY {{ key }}_id) mv_conversions ON mv_conversions.{{ key }}_id=breakdown.{{ key }}_id
LEFT JOIN
    (SELECT {{ key }}_id,
    nvl(sum(conversion_count), 0) AS conversions
    FROM mv_touchpointconversions
    WHERE date = '{{ date }}'
    AND {{ key }}_id IN ({{ value }})
    GROUP BY {{ key }}_id) mv_touchpointconversions ON mv_touchpointconversions.{{ key }}_id=breakdown.{{ key }}_id