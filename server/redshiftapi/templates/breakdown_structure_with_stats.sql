{% load backtosql_tags %}
{% autoescape off %}

SELECT
  {{ breakdown|column_as_alias:"a" }}
FROM {{ view.base }} a
WHERE
    {{ constraints|generate:"a" }}
GROUP BY {{ breakdown|indices }};

{% endautoescape %}