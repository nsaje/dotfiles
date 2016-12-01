{% load backtosql_tags %}
{% autoescape off %}

INSERT INTO {{ destination_table}} (
    SELECT
        {{ breakdown|column_as_alias }},

        a.slug as slug,
        a.conversion_window as conversion_window,
        SUM(a.touchpoint_count) as touchpoint_count,
        SUM(a.conversion_count) as conversion_count

    FROM {{ source_table }} a
    WHERE a.date BETWEEN %(date_from)s AND %(date_to)s
          {% if account_id %}
              AND account_id=%(account_id)s
          {% endif %}
    GROUP BY {{ breakdown|only_alias:"a" }}, a.slug, a.conversion_window
);

{% endautoescape %}