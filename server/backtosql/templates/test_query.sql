{% load backtosql_tags %}

SELECT
  {{ breakdown|column_as_alias:"a" }},
  {{ aggregates|column_as_alias:"a" }}
FROM
  {{ table }} a
WHERE
  a.date_from >= %(date_from)s AND a.date_to <= %(date_to)s
GROUP BY
  {{ breakdown|only_column }},
ORDER BY
  {{ order|only_alias }}
OFFSET %(offset)s
LIMIT %(limit)s