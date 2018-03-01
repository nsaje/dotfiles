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
        CASE
          {% for source_slug, source_id in source_slug_to_id.items %}
          WHEN exchange = '{{ source_slug }}' THEN {{ source_id }}
          {% endfor %}
          ELSE NULL
        END as source_id,
        SUM(bid_reqs),
        SUM(bids),
        SUM(win_notices),
        SUM(total_win_price)

    FROM supply_stats

    WHERE date BETWEEN %(date_from)s AND %(date_to)s
          AND country <> ''
          AND publisher <> ''
          AND device_type > 0
          AND exchange IN (
            {% for source_slug in source_slug_to_id.keys %}
              {% if forloop.last %}
                '{{ source_slug }}'
              {% else %}
                '{{ source_slug }}',
              {% endif %}
            {% endfor %}
          )

    GROUP BY 1, 2, 3, 4

    ORDER BY 1, 2, 3, 4
);

{% endautoescape %}
