{% load backtosql_tags %}
{% autoescape off%}

SELECT {{ breakdown|g_alias:"a" }}, {{ aggregates|g_alias:"a" }}
FROM (
     SELECT
        {{ breakdown|g_w_alias:"b" }}, {{ aggregates|g_w_alias:"b" }},
        ROW_NUMBER() OVER (PARTITION BY {{ breakdown.0|g_alias:"b" }} ORDER BY {{ order|g_alias:"b" }}) AS r1
     FROM
        {{ view }} b
     WHERE {{ constraints|g:"b"}}
     GROUP BY {{ breakdown|g_alias:"b" }}
     ORDER BY {{ order|g_alias:"b" }}
     ) a
WHERE r1 <= %s;
{% endautoescape %}