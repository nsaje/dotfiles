select
    breakdown.{{ key }}_id,
    nvl(sum(impressions), 0) AS impressions,
    nvl(sum(clicks), 0) AS clicks,
    nvl(sum(visits), 0) AS visits,

    nvl(sum(effective_cost_nano::decimal), 0)/1000000000.0 as media,
    nvl(sum(effective_data_cost_nano::decimal), 0)/1000000000.0 as data,
    nvl(sum(license_fee_nano::decimal), 0)/1000000000.0 AS fee,
    nvl(sum(margin_nano::decimal), 0)/1000000000.0 AS margin,
    nvl(sum(conversion_count), 0) as conversions
from mv_adgroup as breakdown
join mv_conversions on mv_conversions.{{ key }}_id=breakdown.{{ key }}_id
and mv_conversions.date=breakdown.date
where breakdown.date = '{{ date }}' AND breakdown.{{ key }}_id IN ({{ value }})
group by breakdown.{{ key }}_id
