select
    {{ key }}_id,
    nvl(sum(impressions), 0) AS impressions,
    nvl(sum(clicks), 0) AS clicks,
    nvl(sum(visits), 0) AS visits,

    nvl(sum(effective_cost_nano::decimal), 0)/1000000000.0 as media,
    nvl(sum(effective_data_cost_nano::decimal), 0)/1000000000.0 as data,
    nvl(sum(license_fee_nano::decimal), 0)/1000000000.0 AS fee,
    nvl(sum(margin_nano::decimal), 0)/1000000000.0 AS margin
from mv_master
where date = '{{ date }}' AND {{ key }}_id IN ({{ value }})
group by {{ key }}_id
