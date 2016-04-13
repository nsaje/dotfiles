{% load backtosql_tags %}

SELECT
  {{ breakdown|g_w_alias:"t" }},
  {{ aggregates|g_w_alias:"t" }}
FROM
  {{ view }} t
WHERE
  t.ad_group_id=ANY(%(ad_group_id)s) AND
  t.dt >= %(date_from)s AND t.dt <= %(date_to)s
    {% for k,v in constraints.items %}
       AND tt.{{k}}=ANY(%({{k}})s)
    {% endfor %}
GROUP BY {{ breakdown|g_alias }};
