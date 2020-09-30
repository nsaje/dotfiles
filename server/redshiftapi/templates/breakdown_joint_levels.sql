{% load backtosql_tags %}
{% autoescape off %}

/* breakdown_joint_levels.sql {{ base_view }}: {{ breakdown|only_column }} */
SELECT
    {{ breakdown|only_alias:"b" }},
    {% if additional_columns %}{{ additional_columns|only_alias:"b" }}, {% endif %}
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
    -- join and rank top rows, then select top rows
    SELECT
          {{ breakdown|only_alias:"a" }},
          {% if additional_columns %}{{ additional_columns|only_alias:"a" }}, {% endif %}
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
              {{ breakdown|only_alias_nullif_zero_value }},  -- no table qualifier in order to automatically select non-null columns from full join
              {% if additional_columns %}{{ additional_columns|column_as_alias }}, {% endif %}
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
              (
                  SELECT
                      {{ breakdown|column_as_alias_coalesce_zero_value:"a" }},
                      {{ aggregates|column_as_alias:"a" }}
                  FROM {{ base_view }} a
                  WHERE
                      {{ constraints|generate:"a" }}
                  GROUP BY {{ breakdown|indices }}
              ) temp_base
              LEFT OUTER JOIN (
                  SELECT
                      {{ breakdown|column_as_alias_coalesce_zero_value:"a" }},
                      {{ yesterday_aggregates|column_as_alias:"a" }}
                  FROM {{ base_view }} a
                  WHERE
                      {{ yesterday_constraints|generate:"a" }}
                  GROUP BY {{ breakdown|indices }}
              ) temp_yesterday USING ({{ breakdown|only_alias }})

              {% if conversions_aggregates %}
              LEFT OUTER JOIN (
                  SELECT
                      {{ breakdown|column_as_alias_coalesce_zero_value:"a" }},
                      {{ conversions_aggregates|column_as_alias:"a" }}
                  FROM {{ conversions_view }} a
                  WHERE
                      {{ conversions_constraints|generate:"a" }}
                  GROUP BY {{ breakdown|indices }}
              ) temp_conversions USING ({{ breakdown|only_alias }})
              {% endif %}

              {% if touchpoints_aggregates %}
              FULL OUTER JOIN (
                  SELECT
                      {{ breakdown|column_as_alias_coalesce_zero_value:"a" }},
                      {{ touchpoints_aggregates|column_as_alias:"a" }}
                  FROM {{ touchpoints_view }} a
                  WHERE
                      {{ touchpoints_constraints|generate:"a" }}
                  GROUP BY {{ breakdown|indices }}
              ) temp_touchpoints USING ({{ breakdown|only_alias }})
              {% endif %}
    ) a
) b
{% if offset is not None and limit is not None %} WHERE {% endif %}
    -- limit number of rows per group (row_number() is 1-based)
    {% if offset is not None %} r >= {{ offset }} + 1 AND {% endif %}
    {% if limit is not None %} r <= {{ limit }} {% endif %}

{% endautoescape %}
