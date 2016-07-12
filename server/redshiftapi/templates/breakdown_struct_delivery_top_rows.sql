{% load backtosql_tags %}
{% autoescape off %}

-- NOTE: this query does not support ordering by conversion fields

-- temporary preselected queries if conversion columns need to be included
WITH
    {% if conversions_aggregates %}
    temp_conversions AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ conversions_aggregates|column_as_alias:"a" }}
        FROM {{ view.conversions }} a
        WHERE
            -- constraints in all queries are generated with the same prefix
            -- so that they maintain the same order (cached generated query in backtosql)
            -- this way params are always correctly ordered
            {{ constraints|generate:"a" }} AND
            {{ breakdown_constraints|generate:"a" }}
        GROUP BY {{ breakdown|only_alias }}
    ),
    {% endif %}

    {% if touchpointconversions_aggregates %}
    temp_touchpointconversions AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ touchpointconversions_aggregates|column_as_alias:"a" }}
            FROM {{ view.touchpointconversions }} a
        WHERE
            {{ constraints|generate:"a" }} AND
            {{ breakdown_constraints|generate:"a" }}
        GROUP BY {{ breakdown|only_alias }}
    ),
    {% endif %}

    -- base query, get all other dimensions and rank them by position
    temp_base AS (
        SELECT
            {{ breakdown|only_alias:"b" }},
            {{ aggregates|only_alias:"b" }}
        FROM (
            SELECT
                {{ breakdown|column_as_alias:"a" }},
                {{ aggregates|column_as_alias:"a" }},
                ROW_NUMBER() OVER (PARTITION BY {{ breakdown_partition|only_column:"a" }}
                ORDER BY {{ order|only_column:"a" }}) AS r
            FROM
                {{ view.base }} a
            WHERE
                {{ constraints|generate:"a"}} AND
                {{ breakdown_constraints|generate:"a" }}
            GROUP BY
                {{ breakdown|only_alias:"a" }}
        ) b
        WHERE
            -- limit number of rows per group (row_number() is 1-based)
            {% if offset %} r >= {{ offset }} + 1 AND {% endif %}
            r <= {{ limit }}
    )

-- join the preselected data together
SELECT
    {{ breakdown|only_alias:"temp_base" }},
    {{ aggregates|only_alias:"temp_base" }}
    {% if conversions_aggregates %}
        ,{{ conversions_aggregates|only_alias:"temp_conversions" }}
    {% endif %}
    {% if touchpointconversions_aggregates %}
        ,{{ touchpointconversions_aggregates|only_alias:"temp_touchpointconversions" }}
    {% endif %}

FROM temp_base
    {% if conversions_aggregates %} NATURAL LEFT OUTER JOIN temp_conversions {% endif %}
    {% if touchpointconversions_aggregates %} NATURAL LEFT OUTER JOIN temp_touchpointconversions {% endif %}

{% endautoescape %}