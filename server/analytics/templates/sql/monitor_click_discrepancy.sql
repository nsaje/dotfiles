SELECT campaign_id, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks) END)*100.0 cd
FROM mv_master
WHERE date >= '{{ from_date }}' AND date <= '{{ till_date }}' AND campaign_id IN ({{ campaigns }})
GROUP BY campaign_id