{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ breakdown|column_as_alias:"a" }},
    {{ aggregates|column_as_alias:"a" }}
FROM
    {{ view }} a
WHERE
    {{ constraints|generate:"a" }}
    {% if breakdown_constraints %}
       AND {{ breakdown_constraints|generate:"a" }}
    {% endif %}
GROUP BY {{ breakdown|only_alias }}
{% if order %}
ORDER BY {{ order|only_alias }}
{% endif %}

{% if limit %}
LIMIT {{ limit }}
{% endif %}
{% if offset %}
OFFSET {{ offset }}
{% endif %}
;
{% endautoescape %}