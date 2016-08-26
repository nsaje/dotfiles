{% load backtosql_tags %}
{% autoescape off %}

WITH
    {% if conversions_aggregates %}
    temp_conversions AS (
        SELECT
            {% if breakdown %} {{ breakdown|column_as_alias:"a" }}, {% endif %}
            {{ conversions_aggregates|column_as_alias:"a" }}
        FROM {{ view.conversions }} a
        WHERE
            -- constraints in all queries are generated with the same prefix
            -- so that they maintain the same order (cached generated query)
            -- this way params are correctly ordered
            {{ constraints|generate:"a" }}
            {% if parent_constraints %}
                AND {{ parent_constraints|generate:"a" }}
            {% endif %}
        -- use indices to refer to breakdown fields, this way if a field name is the same
        -- for source column from database and calculated fields alias the aliase get chosen.
        -- Otherwise the source column is selected and so results are probably not what we
        -- might expect.
        -- Eg: SELECT case table.device_type == 1 then 2 else 1 end AS device_type, ...
        --     FROM table
        --     GROUP BY device_type;  <-- this refers to table.device_type not device_type alias
        {% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
    ),
    {% endif %}

    {% if touchpointconversions_aggregates %}
    temp_touchpointconversions AS (
        SELECT
            {% if breakdown %} {{ breakdown|column_as_alias:"a" }}, {% endif %}
            {{ touchpointconversions_aggregates|column_as_alias:"a" }}
            FROM {{ view.touchpointconversions }} a
        WHERE
            {{ constraints|generate:"a" }}
            {% if parent_constraints %}
                AND {{ parent_constraints|generate:"a" }}
            {% endif %}
        {% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
    ),
    {% endif %}

    {% if yesterday_constraints %}
    temp_yesterday AS (
        SELECT
            {% if breakdown %} {{ breakdown|column_as_alias:"a" }}, {% endif %}
            {{ yesterday_aggregates|column_as_alias:"a" }}
        FROM {{ view.base }} a
        WHERE
            {{ yesterday_constraints|generate:"a" }}
            {% if parent_constraints %}
                AND {{ parent_constraints|generate:"a" }}
            {% endif %}
        {% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
    ),
    {% endif %}

    temp_base AS (
        SELECT
            {% if breakdown %} {{ breakdown|column_as_alias:"a" }}, {% endif %}
            {{ aggregates|column_as_alias:"a" }}

            {% if not yesterday_constraints %}
                ,{{ yesterday_aggregates|column_as_alias:"a" }}
            {% endif %}
        FROM {{ view.base }} a
        WHERE
            {{ constraints|generate:"a" }}
            {% if parent_constraints %}
                AND {{ parent_constraints|generate:"a" }}
            {% endif %}
        {% if breakdown %} GROUP BY {{ breakdown|indices }} {% endif %}
    )
SELECT
    {% if breakdown %} {{ breakdown|only_alias:"temp_base" }}, {% endif %}
    {{ aggregates|only_alias:"temp_base" }},

    {% if yesterday_constraints %}
        {{ yesterday_aggregates|only_alias:"temp_yesterday" }}
    {% else %}
        {{ yesterday_aggregates|only_alias:"temp_base" }}
    {% endif %}

    {% if conversions_aggregates %}
        ,{{ conversions_aggregates|only_alias:"temp_conversions" }}
    {% endif %}

    {% if touchpointconversions_aggregates %}
        ,{{ touchpointconversions_aggregates|only_alias:"temp_touchpointconversions" }}
    {% endif %}
    {% if after_join_conversions_calculations %}
        ,{{ after_join_conversions_calculations|column_as_alias }}
    {% endif %}
FROM
    temp_base
    {% if yesterday_constraints %} NATURAL LEFT JOIN temp_yesterday {% endif %}
    {% if conversions_aggregates %} NATURAL LEFT OUTER JOIN temp_conversions {% endif %}
    {% if touchpointconversions_aggregates %} NATURAL LEFT OUTER JOIN temp_touchpointconversions {% endif %}

{% if order %} ORDER BY {{ order|only_alias }} {% endif %}
{% if limit %} LIMIT {{ limit }} {% endif %}
{% if offset %} OFFSET {{ offset }} {% endif %}
;

{% endautoescape %}