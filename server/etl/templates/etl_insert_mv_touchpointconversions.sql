{% autoescape off %}

INSERT INTO mv_touchpointconversions (
    SELECT
        a.date as date,
        a.source_id as source_id,

        s.agency_id as agency_id,
        s.account_id as account_id,
        s.campaign_id as campaign_id,
        a.ad_group_id as ad_group_id,
        a.content_ad_id as content_ad_id,
        a.publisher as publisher,

        a.slug as slug,
        -- shorter conversion lags are not counted towards longer ones
        -- eg. lag 24 is not conted in the 720
        CASE
            WHEN a.conversion_lag <= 24 THEN 24
            WHEN a.conversion_lag <= 168 THEN 168
            WHEN a.conversion_lag <= 720 THEN 720
            ELSE 2160
        END AS conversion_window,
        count(1) as touchpoint_count

    FROM conversions a join mvh_adgroup_structure s on a.ad_group_id=s.ad_group_id
    WHERE a.conversion_lag <= 2160 AND a.date BETWEEN %(date_from)s AND %(date_to)s
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
);

{% endautoescape %}