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
        CASE
          WHEN device_type = 1 THEN 4  -- when mobile then phone
          WHEN device_type = 6 THEN 3  -- when connected then tv
          WHEN device_type = 7 THEN 3  -- when settopbox then tv
          ELSE device_type
        END as device_type,
        SUM(bid_reqs),
        SUM(bids),
        SUM(win_notices),
        SUM(total_win_price)

    FROM supply_stats

    WHERE date BETWEEN %(date_from)s AND %(date_to)s
          AND country <> ''
          AND publisher <> ''
          AND device_type > 0

    GROUP BY 1, 2, 3

    ORDER BY 1, 2, 3
);

{% endautoescape %}
