{% load backtosql_tags %}
{% autoescape off %}

/* breakdown_joint_base.sql {{ base_view }}: {{ breakdown|only_column }} */
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
        FROM {{ yesterday_view }} a
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

ORDER BY {{ orders|only_alias }}
{% if limit is not None %} LIMIT {{ limit }} {% endif %}
{% if offset is not None %} OFFSET {{ offset }} {% endif %}

{% endautoescape %}
