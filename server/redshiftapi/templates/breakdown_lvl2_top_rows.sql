{% load backtosql_tags %}
{% autoescape off%}

SELECT
    {{ breakdown|only_alias }},
    {{ aggregates|column_as_alias }}
FROM (
    SELECT
        {{ breakdown|column_as_alias:"b" }},
        SUM(b.clicks) clicks,
        SUM(b.impressions) impressions,
        SUM(b.cost_cc) cost_cc,
        SUM(b.data_cost_cc) data_cost_cc,
        SUM(b.effective_cost_nano) effective_cost_nano,
        SUM(b.effective_data_cost_nano) effective_data_cost_nano,
        SUM(b.license_fee_nano) license_fee_nano,
        SUM(b.visits) visits,
        SUM(b.new_visits) new_visits,
        SUM(b.bounced_visits) bounced_visits,
        SUM(b.pageviews) pageviews,
        SUM(b.total_time_on_site) total_time_on_site,
        ROW_NUMBER() OVER (PARTITION BY {{ breakdown.0|only_alias }}, {{ breakdown.1|only_alias }} ORDER BY {{ order|only_column:"b" }}) AS r
    FROM
        {{ view }} b
    WHERE
        -- only select necessary rows
        {{ constraints|generate:"b"}} AND {{ breakdown_constraints|generate:"b" }}
    GROUP BY 1, 2, 3
) a
WHERE
    -- limit number of rows per group (row_number() is 1-based)
    {% if offset %} r >= {{ offset }} + 1 AND {% endif %}
    r <= {{ limit }}
GROUP BY 1, 2, 3
{% endautoescape %}