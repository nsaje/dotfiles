{% load backtosql_tags %}
{% autoescape off %}

WITH
    {% if conversions_aggregates %}
    temp_conversions AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ conversions_aggregates|column_as_alias:"a" }}
        FROM {{ view.conversions }} a
        WHERE
            -- constraints in all queries are generated with the same prefix
            -- so that they maintain the same order (cached generated query)
            -- this way params are correctly ordered
            {{ constraints|generate:"a" }}
            {% if breakdown_constraints %}
                AND {{ breakdown_constraints|generate:"a" }}
            {% endif %}
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
            {{ constraints|generate:"a" }}
            {% if breakdown_constraints %}
                AND {{ breakdown_constraints|generate:"a" }}
            {% endif %}
        GROUP BY {{ breakdown|only_alias }}
    ),
    {% endif %}

    temp_base AS (
        SELECT
            {{ breakdown|column_as_alias:"a" }},
            {{ aggregates|column_as_alias:"a" }}
        FROM {{ view.base }} a
        WHERE
            {{ constraints|generate:"a" }}
            {% if breakdown_constraints %}
                AND {{ breakdown_constraints|generate:"a" }}
            {% endif %}
        GROUP BY {{ breakdown|only_alias }}
    )
SELECT
    {{ breakdown|only_alias:"temp_base" }},
    {{ aggregates|only_alias:"temp_base" }}
    {% if conversions_aggregates %}
        ,{{ conversions_aggregates|only_alias:"temp_conversions" }}
    {% endif %}

    {% if touchpointconversions_aggregates %}
        ,{{ touchpointconversions_aggregates|only_alias:"temp_touchpointconversions" }}
    {% endif %}
FROM
    temp_base
    {% if conversions_aggregates %} NATURAL LEFT OUTER JOIN temp_conversions {% endif %}
    {% if touchpointconversions_aggregates %} NATURAL LEFT OUTER JOIN temp_touchpointconversions {% endif %}

{% if order %} ORDER BY {{ order|only_alias }} {% endif %}
{% if limit %} LIMIT {{ limit }} {% endif %}
{% if offset %} OFFSET {{ offset }} {% endif %}
;

{% endautoescape %}