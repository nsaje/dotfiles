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
        CASE
          WHEN publisher LIKE 'ligatus-network%%' THEN 'Undisclosed Ligatus publishers'
          WHEN publisher LIKE 'AutoCreated%%' THEN 'Undisclosed AppNexus publishers'
          ELSE publisher
        END as publisher,
        CASE
          WHEN device_type = 1 THEN 4  -- when mobile then phone
          ELSE device_type
        END as device_type,
        CASE
          {% for source_slug, source_id in source_slug_to_id.items %}
          WHEN exchange = '{{ source_slug }}' THEN {{ source_id }}
          {% endfor %}
          ELSE NULL
        END as source_id,
        traffic_type as channel,
        SUM(bid_reqs),
        SUM(bids),
        SUM(win_notices),
        SUM(total_win_price),
        SUM(slots),
        SUM(redirects)

    FROM supply_stats

    WHERE date BETWEEN %(date_from)s AND %(date_to)s
          AND country <> ''
          AND publisher <> ''
          AND device_type > 0
          AND device_type NOT IN (3, 6, 7) -- not in tv, connected or settop box
          AND exchange IN (
            {% for source_slug in source_slug_to_id.keys %}
              {% if forloop.last %}
                '{{ source_slug }}'
              {% else %}
                '{{ source_slug }}',
              {% endif %}
            {% endfor %}
          )
          AND (exchange IN (   -- remove exchange condition after supply_stats has correct adstxt_status
              'outbrainrtb',
              'anmsn',
              'msn',
              'rubicon_display',
              'appnexus_display',
              'bsadmixer',
              'bscomet',
              'bswordpress',
              'bsnexage',
              'bsadmedia',
              'bssortable',
              'bsadmatic',
              'bsnetsprint',
              'bsyieldlab',
              'bsoutbrain',
              'bsbrightroll',
              'bskargo',
              'bsmozoo',
              'bstenmax',
              'bsyengo',
              'bsexelbid',
              'bsadview',
              'bsadmax',
              'bsslimcut',
              'adiant',
              'ligatus',
              'smaato',
              'playtem',
              'ividence',
              'livenetlife',
              'prebid',
              'prebid_display'
          ) OR NOT adstxt_status = 'HasAdstxt')

    GROUP BY 1, 2, 3, 4, 5

    ORDER BY 1, 2, 3, 4, 5
);

{% endautoescape %}
