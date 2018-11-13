SELECT ad_group_id
FROM mv_master
WHERE date = '{{ d }}'
GROUP BY ad_group_id
HAVING SUM(effective_cost_nano) >= {{ threshold }}