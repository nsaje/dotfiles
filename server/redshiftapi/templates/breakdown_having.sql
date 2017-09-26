{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {% if breakdown %} {{ breakdown|column_as_alias:"base_table" }}, {% endif %}
    {{ aggregates|column_as_alias:"base_table" }}
FROM
    {{ view }} base_table
WHERE
    {{ constraints|generate:"base_table" }}
{% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
{% if having %} HAVING {{ having|generate:"base_table" }} {% endif %}
ORDER BY {{ orders|only_alias }}

{% endautoescape %}
