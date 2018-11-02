SELECT account_id,
       (sum(cost_nano) - sum(effective_cost_nano)) +
       (sum(data_cost_nano) - sum(effective_data_cost_nano)) as diff
FROM mv_account
WHERE date = '{{ date }}'
GROUP BY account_id
HAVING sum(cost_nano) - sum(effective_cost_nano) > {{ threshold }} or
       sum(data_cost_nano) - sum(effective_data_cost_nano) > {{ threshold }}