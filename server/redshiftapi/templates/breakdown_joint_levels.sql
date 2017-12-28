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
        FROM {{ base_view }} a
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
    {{ breakdown|only_alias:"b" }},
    {{ aggregates|only_alias:"b" }},
    {{ yesterday_aggregates|only_alias:"b" }}

    {% if conversions_aggregates %}
        ,{{ conversions_aggregates|only_alias:"b" }}
    {% endif %}

    {% if touchpoints_aggregates %}
        ,{{ touchpoints_aggregates|only_alias:"b" }}
    {% endif %}

    {% if after_join_aggregates %}
        ,{{ after_join_aggregates|only_alias:"b" }}
    {% endif %}

FROM (
    -- join and rank top rows, than select top rows
    SELECT
          {{ breakdown|only_alias:"a" }},
          {{ aggregates|only_alias:"a" }},
          {{ yesterday_aggregates|only_alias:"a" }}

          {% if conversions_aggregates %}
              ,{{ conversions_aggregates|only_alias:"a" }}
          {% endif %}

          {% if touchpoints_aggregates %}
              ,{{ touchpoints_aggregates|only_alias:"a" }}
          {% endif %}

          {% if after_join_aggregates %}
              ,{{ after_join_aggregates|only_alias:"a" }}
          {% endif %}
          -- asd
          , ROW_NUMBER() OVER (PARTITION BY {{ partition|only_alias:"a" }}
          ORDER BY {{ orders|only_alias:"a" }}) AS r
     FROM
     (
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
              temp_base NATURAL LEFT OUTER JOIN temp_yesterday
              {% if conversions_aggregates %} NATURAL LEFT OUTER JOIN temp_conversions {% endif %}
              {% if touchpoints_aggregates %} NATURAL LEFT OUTER JOIN temp_touchpoints {% endif %}
    ) a
) b
WHERE
    -- limit number of rows per group (row_number() is 1-based)
    {% if offset %} r >= {{ offset }} + 1 AND {% endif %}
    {% if limit %} r <= {{ limit }} {% endif %}

{% endautoescape %}
