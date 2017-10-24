{% autoescape off %}

INSERT INTO mv_touchpointconversions (
    SELECT
        a.date as date,
        a.source_id as source_id,

        s.account_id as account_id,
        s.campaign_id as campaign_id,
        a.ad_group_id as ad_group_id,
        a.content_ad_id as content_ad_id,

        CASE WHEN a.source_id = {{ outbrain_id }} THEN a.publisher
             WHEN a.source_id = {{ yahoo_id }} THEN 'all publishers'
             ELSE LOWER(a.publisher)
        END AS publisher,
        CASE WHEN a.source_id = {{ outbrain_id }} THEN NVL(a.publisher, '') || '__{{ outbrain_id }}'
             WHEN a.source_id = {{ yahoo_id }} THEN 'all publishers__{{ yahoo_id }}'
             ELSE LOWER(NVL(a.publisher, '')) || '__' || a.source_id
        END AS publisher_source_id,

        a.slug as slug,
        -- shorter conversion lags are not counted towards longer ones
        -- eg. lag 24 is not counted in the 720
        CASE
            WHEN a.conversion_lag <= 24 THEN 24
            WHEN a.conversion_lag <= 168 THEN 168
            WHEN a.conversion_lag <= 720 THEN 720
            ELSE 2160
        END AS conversion_window,
        a.conversion_label as conversion_label,

        COUNT(a.touchpoint_id) as touchpoint_count,
        SUM(CASE WHEN a.conversion_id_ranked = 1 THEN 1 ELSE 0 END) AS conversion_count,
        SUM(a.conversion_value_nano) as conversion_value_nano
    FROM (
        SELECT
              c.date as date,
              c.source_id as source_id,

              c.ad_group_id as ad_group_id,
              c.content_ad_id as content_ad_id,
              c.publisher as publisher,

              c.slug as slug,

              c.conversion_lag as conversion_lag,

              c.touchpoint_id as touchpoint_id,
              RANK() OVER
                  (PARTITION BY c.conversion_id, c.ad_group_id ORDER BY c.touchpoint_timestamp DESC) AS conversion_id_ranked,

              c.value_nano as conversion_value_nano,
              c.label as conversion_label
        FROM conversions c
        WHERE c.conversion_lag <= 2160 AND c.date BETWEEN %(date_from)s AND %(date_to)s
              {% if account_id %}
                  AND c.account_id=%(account_id)s
              {% endif %}
    ) a join mvh_adgroup_structure s on a.ad_group_id=s.ad_group_id
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
);

{% endautoescape %}
