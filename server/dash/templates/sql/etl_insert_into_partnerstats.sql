INSERT INTO partnerstats 
(
  SELECT convert_timezone('UTC', 'America/New_York',
                          (date || ' ' || hour || ':00:00')::timestamp)::date as date,
         date as utc_date,
         hour as utc_hour,
         media_source as exchange,
         outbrain_section_id,
         outbrain_publisher_id,
         publisher,
         sum(impressions) AS impressions,
         sum(clicks) AS clicks,

         SUM(spend)*1000 AS cost_nano,
         SUM(original_spend)*1000 AS original_cost_nano,
         SUM(ssp_spend)*1000 AS ssp_cost_nano
   FROM (SELECT * FROM stats_diff UNION ALL SELECT * FROM stats) AS stats
   WHERE date >= (current_date - interval '1 day') AND media_source NOT IN ('outbrain', 'yahoo')
   GROUP BY 1, 2, 3, 4, 5, 6, 7
);
