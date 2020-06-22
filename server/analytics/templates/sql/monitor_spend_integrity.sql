SELECT
    sum(effective_cost_nano) as base_media,
    sum(effective_data_cost_nano) as base_data,
    SUM(service_fee_nano) AS service_fee,
    SUM(license_fee_nano) AS license_fee,
    SUM(margin_nano) AS margin
FROM
    {{ tbl }}
WHERE
    date = '{{ d }}'{{ additional }}
