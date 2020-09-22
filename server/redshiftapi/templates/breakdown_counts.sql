{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {% if parent_breakdown %} {{ parent_breakdown|column_as_alias:"temp_base_table" }}, {% endif %}
    COUNT(*)
FROM (
    SELECT
        {% if breakdown %} {{ breakdown|column_as_alias:"base_table" }} {% endif %}
    FROM
        {{ view }} base_table
    WHERE
        {{ constraints|generate:"base_table" }}
    {% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
) temp_base_table
{% if parent_breakdown %} GROUP BY {{ parent_breakdown|indices }} {% endif %}

{% endautoescape %}
