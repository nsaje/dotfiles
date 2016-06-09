{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ breakdown|column_as_alias }},
    {{ aggregates|column_as_alias }}
FROM
    {{ table }}
WHERE
    date=%(date)s
GROUP BY
    {{ breakdown|only_alias }};

{% endautoescape %}