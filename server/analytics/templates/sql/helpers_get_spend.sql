select
    sum(effective_cost_nano::decimal)/1000000000.0 as media,
    sum(effective_data_cost_nano::decimal)/1000000000.0 as data,
    sum(service_fee_nano::decimal)/1000000000.0 AS service_fee,
    sum(license_fee_nano::decimal)/1000000000.0 AS fee,
    sum(margin_nano::decimal)/1000000000.0 AS margin
from mv_master
where date >= '{{ date }}' AND {{ key }}_id {{ operator }} {{ value }};
