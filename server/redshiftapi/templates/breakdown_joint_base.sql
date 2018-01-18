{% load backtosql_tags %}
{% autoescape off %}

WITH
    {% if conversions_aggregates %}
    temp_conversions AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ conversions_aggregates|column_as_alias:"a" }}
        FROM {{ conversions_view }} a
        WHERE
            {{ conversions_constraints|generate:"a" }}
        GROUP BY {{ breakdown|indices }}
    ),
    {% endif %}

    {% if touchpoints_aggregates %}
    temp_touchpoints AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ touchpoints_aggregates|column_as_alias:"a" }}
        FROM {{ touchpoints_view }} a
        WHERE
            {{ touchpoints_constraints|generate:"a" }}
        GROUP BY {{ breakdown|indices }}
    ),
    {% endif %}

    temp_yesterday AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ yesterday_aggregates|column_as_alias:"a" }}
        FROM {{ yesterday_view }} a
        WHERE
            {{ yesterday_constraints|generate:"a" }}
        GROUP BY {{ breakdown|indices }}
    ),

    temp_base AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ aggregates|column_as_alias:"a" }}
        FROM {{ base_view }} a
        WHERE
            {{ constraints|generate:"a" }}
        GROUP BY {{ breakdown|indices }}
    )
SELECT
    {{ breakdown|only_alias:"temp_base" }},
    {{ aggregates|only_alias:"temp_base" }},
    {{ yesterday_aggregates|only_alias:"temp_yesterday" }}

    {% if conversions_aggregates %}
        ,{{ conversions_aggregates|only_alias:"temp_conversions" }}
    {% endif %}

    {% if touchpoints_aggregates %}
        ,{{ touchpoints_aggregates|only_alias:"temp_touchpoints" }}
    {% endif %}

    {% if after_join_aggregates %}
        ,{{ after_join_aggregates|column_as_alias }}
    {% endif %}
FROM
    temp_base LEFT OUTER JOIN temp_yesterday ON {{ breakdown|columns_equal_or_null:"temp_base,temp_yesterday" }}
    {% if conversions_aggregates %}
        LEFT OUTER JOIN temp_conversions ON {{ breakdown|columns_equal_or_null:"temp_base,temp_conversions" }}
    {% endif %}
    {% if touchpoints_aggregates %}
        LEFT OUTER JOIN temp_touchpoints ON {{ breakdown|columns_equal_or_null:"temp_base,temp_touchpoints" }}
    {% endif %}

ORDER BY {{ orders|only_alias }}
{% if limit %} LIMIT {{ limit }} {% endif %}
{% if offset %} OFFSET {{ offset }} {% endif %}

{% endautoescape %}
