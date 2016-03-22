{% load query_helpers %}
SELECT
  {{ breakdowns|pfx:"t"|join:"," }},
  {{ aggregates|pfx:"t"|join:"," }}
FROM
  {{ view }} t
WHERE
  t.adgroup_id=ANY(%(ad_group_id)s) AND
  t.date>=%(date_from)s AND t.date<=%(date_to)s
GROUP BY 1;
