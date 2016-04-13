{% load backtosql_tags %}

SELECT
  {{ breakdown|g_w_alias:"a" }},
  {{ aggregates|g_w_alias:"a" }}
FROM
  {{ table }} a
WHERE
  a.date_from >= %(date_from)s AND a.date_to <= %(date_to)s
GROUP BY
  {{ breakdown|g }},
ORDER BY
  {{ order|g_alias }}
OFFSET %(offset)s
LIMIT %(limit)s