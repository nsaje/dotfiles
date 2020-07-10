SELECT *
FROM
  (SELECT publisher, date, sum(impressions) AS impressions,
                           sum(clicks) AS clicks,
                           sum(case when source_id = 59 then clicks else 0 end) as adx_clicks,
                           ((sum(clicks) :: decimal / nullif(sum(impressions) :: decimal, 0)) * 100) :: decimal AS ctr
   FROM mv_master
   GROUP BY publisher, date ) ctr_query
WHERE date = '{{ date }}' AND (
    (clicks > {{ max_clicks }}
      AND impressions > {{ max_impressions }}
      AND ctr >= {{ ctr_threshold }})
    OR (ctr >= 30 AND clicks >= 50)
  ) AND (adx_clicks*1.0/(clicks+1) <= 0.2 OR adx_clicks >= 100);
