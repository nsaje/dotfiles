{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ breakdown|g_w_alias:"a" }},
    {{ aggregates|g_w_alias:"a" }}
FROM
    {{ view }} a
WHERE
    {{ constraints|g:"a" }}
    {% if breakdown_constraints %}
       AND {{ breakdown_constraints|g:"a" }}
    {% endif %}
GROUP BY {{ breakdown|g_alias }}
{% if order %}
ORDER BY {{ order|g_alias }}
{% endif %}

{% if limit %}
LIMIT {{ limit }}
{% endif %}
{% if offset %}
OFFSET {{ offset }}
{% endif %}
;
{% endautoescape %}