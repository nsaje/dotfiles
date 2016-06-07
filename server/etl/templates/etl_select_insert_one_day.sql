{% load backtosql_tags %}
{% autoescape off %}

INSERT INTO {{ destination_table }}
(
    SELECT
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ source_table }}
    WHERE
        date=%(date)s
    GROUP BY
        {{ breakdown|only_alias }}
);

{% endautoescape %}
