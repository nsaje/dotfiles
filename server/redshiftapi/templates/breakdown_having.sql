{% load backtosql_tags %}
{% autoescape off %}

/* breakdown_having.sql {{ view }}: {{ breakdown|only_column }}*/
SELECT
    {% if breakdown %} {{ breakdown|column_as_alias:"base_table" }}, {% endif %}
    {{ aggregates|column_as_alias:"base_table" }}
    {% if additional_columns %}{{ additional_columns|column_as_alias }}, {% endif %}
FROM
    {{ view }} base_table
WHERE
    {{ constraints|generate:"base_table" }}
{% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
{% if having %} HAVING {{ having|generate:"base_table" }} {% endif %}
ORDER BY {{ orders|only_alias }}

{% endautoescape %}
