{% load backtosql_tags %}
{% autoescape off%}

SELECT
    ---- get name of column with a reference to another table and alias
    {{ breakdown.0|g_alias:"a" }},
    CASE WHEN -- selects X items from a breakdown and collects others in a joint row
            {% if offset %}
              r >= {{ offset }} AND
            {% endif %}
            r <= {{ limit }}
          THEN {{ breakdown.1|g_alias:"a" }}
        ELSE -1
    END AS {{ breakdown.1|g_alias }},
    {{ aggregates|g_w_alias:"a" }}
FROM (
    SELECT
        {{ breakdown|g_w_alias:"b" }},
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
        ROW_NUMBER() OVER (PARTITION BY {{ breakdown.0|g:"b" }} ORDER BY {{ order|g:"b" }}) AS r
    FROM
        {{ view }} b
    WHERE
        {{ constraints|g:"b"}}
    GROUP BY
        --- get name of column by alias
        {{ breakdown|g_alias }}
) a
GROUP BY 1, 2
{% endautoescape %}