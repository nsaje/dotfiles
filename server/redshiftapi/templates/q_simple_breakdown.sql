{% load backtosql_tags %}
{% autoescape off %}
SELECT {{ breakdown|g_w_alias:"a" }}, {{ aggregates|g_w_alias:"a" }}
FROM {{ view }} a
WHERE {{ constraints|g:"a" }}
{% if order %}
ORDER BY {{ order|g_alias:"a" }}
{% endif %}
{% if offset %}
OFFSET %s
{% endif %}
{% if limit %}
LIMIT %s
{% endif %}
;
{% endautoescape %}