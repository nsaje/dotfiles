SELECT sum(effective_cost_nano) as media, sum(effective_data_cost_nano) as data, SUM(license_fee_nano) AS fee, SUM(margin_nano) AS margin
FROM {{ tbl }}
WHERE date = '{{ d }}'{{ additional }}
