{% load backtosql_tags %}
{% autoescape off%}

SELECT
    {{ breakdown.0|g_alias }},
    {{ breakdown.1|g_alias }},
    CASE WHEN
    {% if offset %}
    r >= {{ offset }} AND
    {% endif %}
    {% if limit %}
    r <= {{ limit }}
    {% endif %} THEN {{ breakdown.2|g_alias }} ELSE -1 END AS {{ breakdown.2|g_alias }},
    {{ aggregates|g_w_alias }}
FROM (
    SELECT
        {{ breakdown.0|g_w_alias:"b" }},
        CASE WHEN {{ breakdown_constraints|g:"b" }} THEN {{ breakdown.1|g:"b" }} ELSE -1 END AS {{ breakdown.1|g_alias}},
        {{ breakdown.2|g_w_alias:"b" }},
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
        ROW_NUMBER() OVER (PARTITION BY {{ breakdown.0|g_alias }}, {{ breakdown.1|g_alias }} ORDER BY {{ order|g:"b" }}) AS r
    FROM
        {{ view }} b
    WHERE
        {{ constraints|g:"b"}}
    GROUP BY 1, 2, 3
) a
GROUP BY 1, 2, 3
{% endautoescape %}