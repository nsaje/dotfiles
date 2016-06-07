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
        date BETWEEN %(date_from)s AND %(date_to)s
    GROUP BY
        {{ breakdown|only_alias }}
);

{% endautoescape %}
