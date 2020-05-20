SELECT {{breakdown}},
       SUM(impressions) AS impressions,
       SUM(clicks) AS clicks,
       SUM(spend) AS spend
FROM (
  SELECT date,
         exchange,
         publisher,
         SUM(impressions) as impressions,
         SUM(clicks) AS clicks,
         SUM(ssp_cost_nano::decimal)/1e9 as spend
  FROM partnerstats
  WHERE {% if bidder_slug %}exchange = '{{bidder_slug}}'{% else %}1=1{% endif %}
{% if outbrain_publisher_ids %}
        AND outbrain_publisher_id IN ({{outbrain_publisher_ids|safe}})
{% endif %}
  GROUP BY 1, 2, 3
) stats
WHERE date BETWEEN '{{ start_date }}' AND '{{ end_date }}'
GROUP BY {{breakdown}}
ORDER BY {{breakdown}}
