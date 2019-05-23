{% load backtosql_tags %}
{% autoescape off %}

INSERT INTO {{ destination_table }}
(
    {{ breakdown|only_alias }},
    {{ aggregates|only_alias }}
)
(
    SELECT
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ source_table }}
    WHERE
        {{ constraints|generate }}
    GROUP BY
        {{ breakdown|only_alias }}
    ORDER BY
        {{ order|only_alias }}
);

{% endautoescape %}
