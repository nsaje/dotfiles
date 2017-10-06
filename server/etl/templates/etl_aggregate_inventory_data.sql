{% autoescape off %}

INSERT INTO mv_inventory (
    SELECT
        CASE
          WHEN country IN (
            {% for country_code in valid_country_codes %}
              {% if forloop.last %}
                '{{ country_code }}'
              {% else %}
                '{{ country_code }}',
              {% endif %}
            {% endfor %}
          ) THEN country
          ELSE NULL
        END as country,
        publisher,
        device_type,
        SUM(bid_reqs),
        SUM(bids),
        SUM(win_notices),
        SUM(total_win_price)

    FROM supply_stats

    WHERE date BETWEEN %(date_from)s AND %(date_to)s

    GROUP BY 1, 2, 3

    ORDER BY 1, 2, 3
);

{% endautoescape %}
