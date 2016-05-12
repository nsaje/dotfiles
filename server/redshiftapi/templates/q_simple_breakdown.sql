{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ breakdown|g_w_alias:"a" }},
    {{ aggregates|g_w_alias:"a" }}
FROM
    {{ view }} a
WHERE
    {{ constraints|g:"a" }}
GROUP BY {{ breakdown|g_alias:"a" }}
{% if order %}
ORDER BY {{ order|g_alias:"a" }}
{% endif %}

{% if limit %}
LIMIT {{ limit }}
{% endif %}
{% if offset %}
OFFSET {{ offset }}
{% endif %}
;

{% endautoescape %}