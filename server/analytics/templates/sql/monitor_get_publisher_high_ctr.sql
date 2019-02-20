SELECT *
FROM
  (SELECT publisher, date, sum(impressions) AS impressions,
                           sum(clicks) AS clicks,
                           ((sum(clicks) :: decimal / nullif(sum(impressions) :: decimal, 0)) * 100) :: decimal AS ctr
   FROM mv_master_pubs
   GROUP BY publisher, date ) ctr_query
WHERE date = '{{ date }}'
  AND clicks > {{ max_clicks }}
  AND impressions > {{ max_impressions }}
  AND ctr >= {{ ctr_threshold }};