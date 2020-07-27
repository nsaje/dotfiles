{% load backtosql_tags %}
{% autoescape off %}

(
    SELECT
        {{ last_day_key }} as window_key,
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ target_type_table }}
    WHERE
        ad_group_id IN ({{ ad_group_ids }})
        AND date >= '{{ last_day_date_from|date:"Y-m-d" }}'
    GROUP BY
        ad_group_id,
        {{ target_type_group_columns }}
) UNION ALL (
    SELECT
        {{ last_3_days_key }} as window_key,
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ target_type_table }}
    WHERE
        ad_group_id IN ({{ ad_group_ids }})
        AND date >= '{{ last_3_days_date_from|date:"Y-m-d" }}'
    GROUP BY
        ad_group_id,
        {{ target_type_group_columns }}
) UNION ALL (
    SELECT
        {{ last_7_days_key }} as window_key,
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ target_type_table }}
    WHERE
        ad_group_id IN ({{ ad_group_ids }})
        AND date >= '{{ last_7_days_date_from|date:"Y-m-d" }}'
    GROUP BY
        ad_group_id,
        {{ target_type_group_columns }}
) UNION ALL (
    SELECT
        {{ last_30_days_key }} as window_key,
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ target_type_table }}
    WHERE
        ad_group_id IN ({{ ad_group_ids }})
        AND date >= '{{ last_30_days_date_from|date:"Y-m-d" }}'
    GROUP BY
        ad_group_id,
        {{ target_type_group_columns }}
) UNION ALL (
    SELECT
        {{ last_60_days_key }} as window_key,
        {{ breakdown|column_as_alias }},
        {{ aggregates|column_as_alias }}
    FROM
        {{ target_type_table }}
    WHERE
        ad_group_id IN ({{ ad_group_ids }})
        AND date >= '{{ last_60_days_date_from|date:"Y-m-d" }}'
    GROUP BY
        ad_group_id,
        {{ target_type_group_columns }}
)

{% endautoescape %}
