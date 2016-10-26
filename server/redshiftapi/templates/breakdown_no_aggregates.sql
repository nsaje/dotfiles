{% load backtosql_tags %}
{% autoescape off %}

SELECT
  {{ breakdown|column_as_alias:"base_table" }}
FROM {{ view }} base_table
WHERE
    {{ constraints|generate:"base_table" }}
GROUP BY {{ breakdown|indices }};

{% endautoescape %}