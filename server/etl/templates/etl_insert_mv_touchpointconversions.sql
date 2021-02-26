{% autoescape off %}

INSERT INTO mv_touchpointconversions (
    SELECT
        a.date as date,

        CASE WHEN a.date > '2022-01-01' and s.uses_source_groups THEN b.parent_source_id --Date will be changed when merged
            ELSE a.source_id
        END as source_id,

        s.account_id as account_id,
        s.campaign_id as campaign_id,
        a.ad_group_id as ad_group_id,
        a.content_ad_id as content_ad_id,

        LOWER(a.publisher) AS publisher,
        LOWER(COALESCE(a.publisher, '')) || '__' || a.source_id AS publisher_source_id,

        -- IMPORTANT: the delivery dimensions cleanup should be kept in sync with how it is
        -- cleaned in etl_insert_mv_master_stats
        CASE WHEN a.device_type = 1 THEN 4  -- convert legacy OpenRTB `mobile` to `phone`
             WHEN a.device_type = 6 THEN 3
             WHEN a.device_type = 7 THEN 3
             ELSE NULLIF(a.device_type, 0)
        END AS device_type,
        CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
            WHEN a.device_os ILIKE '%%unknown%%' THEN NULL
            WHEN a.device_os ILIKE 'Android%%' THEN 'Android'
            WHEN a.device_os ILIKE 'iOS%%' THEN 'iOS'
            WHEN a.device_os ILIKE 'WinPhone%%' THEN 'WinPhone'
            WHEN a.device_os ILIKE 'WinRT%%' THEN 'WinRT'
            WHEN a.device_os ILIKE 'Windows%%' THEN 'Windows'
            WHEN a.device_os ILIKE 'MacOSX%%' THEN 'macOS'
            WHEN a.device_os ILIKE 'macOS%%' THEN 'macOS'
            WHEN a.device_os IN ('Linux', 'Ubuntu', 'Debian', 'Fedora') THEN 'Linux'
            WHEN a.device_os ILIKE 'ChromeOS' THEN 'ChromeOS'
            WHEN NULLIF(TRIM(a.device_os), '') IS NOT NULL THEN 'Other'
            ELSE NULL
        END AS device_os,
        CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
            WHEN a.device_os_version ILIKE '%%unknown%%' THEN NULL
            WHEN a.device_os_version ILIKE 'Android%%' THEN a.device_os_version
            WHEN a.device_os_version ILIKE 'iOS%%' THEN REPLACE(a.device_os_version, ';', '')  -- some special case
            WHEN a.device_os_version ILIKE 'WinPhone%%' THEN a.device_os_version
            WHEN a.device_os_version ILIKE 'WinRT%%' THEN a.device_os_version
            WHEN a.device_os_version ILIKE 'Windows%%' THEN a.device_os_version
            WHEN a.device_os_version ILIKE 'MacOS%%' THEN a.device_os_version
            WHEN a.device_os_version ILIKE 'ChromeOS%%' THEN a.device_os_version
            WHEN NULLIF(TRIM(a.device_os_version), '') IS NOT NULL THEN 'Other'
            ELSE NULL
        END AS device_os_version,
        NULLIF(TRIM(a.environment), '') as environment,

        NULLIF(TRIM(UPPER(a.country)), '') AS country,
        CASE WHEN a.state ILIKE '%%-%%' THEN NULLIF(TRIM(UPPER(a.state)), '')
             ELSE NULLIF(TRIM(UPPER(a.country)), '') || '-' || NULLIF(TRIM(UPPER(a.state)), '')
        END AS state,
        CASE WHEN a.country ILIKE 'US' AND a.dma BETWEEN 500 AND 882 THEN a.dma
             ELSE NULL
        END AS dma,

        a.slug as slug,

        -- shorter conversion lags are not counted towards longer ones
        -- eg. lag 24 is not counted in the 720
        CASE
            WHEN a.conversion_lag <= 24 THEN 24
            WHEN a.conversion_lag <= 168 THEN 168
            ELSE 720
        END AS conversion_window,

        a.conversion_label as conversion_label,

        COUNT(a.touchpoint_id) as touchpoint_count,
        SUM(CASE WHEN a.conversion_id_ranked = 1 THEN 1 ELSE 0 END) AS conversion_count,
        SUM(a.conversion_value_nano) as conversion_value_nano,

        a.type as type,
        CASE WHEN TRIM(a.placement)='' THEN NULL ELSE a.placement END AS placement,
        NULLIF(a.placement_type, 0) as placement_type,

        CASE WHEN a.browser = 'ucBrowser' THEN 'UC_BROWSER'
            ELSE NULLIF(TRIM(UPPER(a.browser)), '')
        END as browser,

        CASE WHEN a.connection_type IN ('cableDSL', 'corporate', 'dialup') THEN 'wifi'
            WHEN a.connection_type = 'cellular' THEN 'cellular'
            ELSE NULL
        END as connection_type,
        a.source_id as original_source_id
    FROM (
        SELECT
              c.date as date,
              c.source_id as source_id,

              c.ad_group_id as ad_group_id,
              c.content_ad_id as content_ad_id,
              c.publisher as publisher,

              c.device_type as device_type,
              c.device_os as device_os,
              c.device_os_version as device_os_version,
              c.environment as environment,
              c.browser as browser,
              c.connection_type as connection_type,

              c.country as country,
              c.state as state,
              c.dma as dma,

              c.slug as slug,

              c.conversion_lag as conversion_lag,

              c.touchpoint_id as touchpoint_id,

              -- rank is used so we can only take the last conversion of the highest priority type (click is higher priority than view) in the main query
              RANK() OVER
                  (PARTITION BY c.conversion_id, c.ad_group_id, c.type ORDER BY c.touchpoint_timestamp DESC, c.type ASC) AS conversion_id_ranked,

              c.value_nano as conversion_value_nano,
              c.label as conversion_label,
              c.type as type,
              c.placement as placement,
              c.placement_type as placement_type
        FROM conversions c
        WHERE c.conversion_lag <= 720 AND c.date BETWEEN %(date_from)s AND %(date_to)s
              {% if account_id %}
                  AND c.account_id=%(account_id)s
              {% endif %}
    ) a
    left outer join mvh_source b on a.source_id=b.source_id
    join mvh_adgroup_structure s on a.ad_group_id=s.ad_group_id

    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 22, 23, 24, 25, 26, 27
);

{% endautoescape %}
