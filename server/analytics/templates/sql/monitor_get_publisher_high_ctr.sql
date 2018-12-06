SELECT *
FROM (SELECT publisher,
             date,
             sum(impressions) as impressions,
             sum(clicks) as clicks,
             ((sum(clicks) :: decimal / nullif(sum(impressions) :: decimal, 0)) * 100) :: decimal as ctr
      FROM stats
      WHERE date = '{{ date }}'
      AND clicks > {{ max_clicks }}
      AND impressions > {{ max_impressions }}
      group by publisher, date
     ) ctr_query
WHERE ctr >= {{ ctr_threshold }};