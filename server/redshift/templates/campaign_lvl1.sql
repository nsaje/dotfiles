{% load breakdown_tags backtosql_tags %}

SELECT {{ breakdowns|gen|join:"," }},{{ aggregates|gen:"t"|join:"," }}
FROM {{ view }} t
WHERE
  t.adgroup_id=ANY(%(ad_group_id)s) AND
  t.date>=%(date_from)s AND t.date<=%(date_to)s
GROUP BY {{ breakdowns|indices|join:","}};