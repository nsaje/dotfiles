{% load backtosql_tags %}
{% autoescape off %}

/* breakdown.sql {{ view }}: {{ breakdown|only_column }}*/
SELECT
    {% if breakdown %} {{ breakdown|column_as_alias }}, {% endif %}
    {% if additional_columns %}{{ additional_columns|column_as_alias }}, {% endif %}
    {{ aggregates|column_as_alias:"base_table" }}
FROM
    {{ view }} base_table
WHERE
    {{ constraints|generate:"base_table" }}
{% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
ORDER BY {{ orders|only_alias }}

{% endautoescape %}
