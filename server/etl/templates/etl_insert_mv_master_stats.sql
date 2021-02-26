{% autoescape off %}

INSERT INTO mv_master (
    SELECT
        a.date,

        CASE WHEN a.date > '2022-01-01' and c.uses_source_groups THEN b.parent_source_id --Date will be changed when merged
            ELSE b.source_id
        END as source_id,

        c.account_id,
        c.campaign_id,
        a.ad_group_id,
        a.content_ad_id,

        a.publisher,
        COALESCE(a.publisher, '') || '__' || b.source_id as publisher_source_id,

        -- When adding new breakdown dimensions, add them to natural full outer join with mv_touchpointconversions below
        -- too!
        a.device_type,
        a.device_os,
        a.device_os_version,
        a.environment,

        a.zem_placement_type,
        a.video_playback_method,

        a.country,
        a.state,
        a.dma,
        a.city_id,

        a.age as age,
        a.gender as gender,
        a.age_gender as age_gender,

        a.impressions as impressions,
        a.clicks as clicks,
        -- convert micro to nano
        a.spend::bigint * 1000 as cost_nano,
        a.data_spend::bigint * 1000 as data_cost_nano,

        null as visits,
        null as new_visits,
        null as bounced_visits,
        null as pageviews,
        null as total_time_on_site,

        round(
            (a.spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
        ) as effective_cost_nano,
        round(
            (a.data_spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
        ) as effective_data_cost_nano,
        round(
          round(
            (
              (nvl(a.spend, 0) + nvl(a.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
            ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
          )::bigint * cf.pct_license_fee::decimal(10, 8)
        ) as license_fee_nano,
        round(
          (
            round(
              (
                (nvl(a.spend, 0) + nvl(a.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
              ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
            )::bigint * (1 + cf.pct_license_fee::decimal(10, 8)) -- add license fee
          ) * cf.pct_margin::decimal(10, 8)
        ) as margin_nano,

        null as users,
        null as returning_users,

        a.video_start as video_start,
        a.video_first_quartile as video_first_quartile,
        a.video_midpoint as video_midpoint,
        a.video_third_quartile as video_third_quartile,
        a.video_complete as video_complete,
        a.video_progress_3s as video_progress_3s,

        round(a.spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_cost_nano,
        round(a.data_spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_data_cost_nano,
        -- casting intermediate values to bigint (decimal(19, 0)) because of max precision of 38 in DB
        round(
            round(
                (a.spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_effective_cost_nano,
        round(
            round(
                (a.data_spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_effective_data_cost_nano,
        round(
          (
            round(
              (
                (nvl(a.spend, 0) + nvl(a.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
              ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
            )::bigint * cf.pct_license_fee::decimal(10, 8)
          ) * cer.exchange_rate::decimal(10, 4)
        ) as local_license_fee_nano,
        round(
          (
            (
              round(
                (
                  (nvl(a.spend, 0) + nvl(a.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
                ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
              )::bigint * (1 + cf.pct_license_fee::decimal(10, 8)) -- add license fee
            ) * cf.pct_margin::decimal(10, 8)
          ) * cer.exchange_rate::decimal(10, 4)
        ) as local_margin_nano,

        a.mrc50_measurable as mrc50_measurable,
        a.mrc50_viewable as mrc50_viewable,
        a.mrc100_measurable as mrc100_measurable,
        a.mrc100_viewable as mrc100_viewable,
        a.vast4_measurable as vast4_measurable,
        a.vast4_viewable as vast4_viewable,

        a.ssp_spend::bigint * 1000 as ssp_cost_nano,
        round(a.ssp_spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_ssp_cost_nano,

        round(a.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as base_effective_cost_nano,
        round(a.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as base_effective_data_cost_nano,
        round(
            (
                (nvl(a.spend, 0) + nvl(a.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) -- effective spend
            ) * cf.pct_service_fee::decimal(10, 8) * 1000
        ) as service_fee_nano,

        round(
            round(a.spend * cf.pct_actual_spend::decimal(10, 8) * 1000)::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_base_effective_cost_nano,
        round(
            round(a.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000)::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_base_effective_data_cost_nano,
        round(
            round(
                (
                    (nvl(a.spend, 0) + nvl(a.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) -- effective spend
                ) * cf.pct_service_fee::decimal(10, 8) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_service_fee_nano,
        a.browser,
        a.connection_type,
        a.outbrain_publisher_id,
        a.outbrain_section_id,
        b.source_id as original_source_id
    FROM
        (
            SELECT
                CASE
                    WHEN hour is null THEN date
                    WHEN hour is not null AND (
                        (date=%(tzdate_from)s AND hour >= %(tzhour_from)s) OR
                        (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
                    )
                    THEN %(date)s
                END as date,
                stats.media_source as source_slug,

                ad_group_id,
                content_ad_id,
                LOWER(publisher) as publisher,

                CASE WHEN device_type = 1 THEN 4  -- convert legacy OpenRTB `mobile` to `phone`
                    WHEN device_type = 6 THEN 3
                    WHEN device_type = 7 THEN 3
                    ELSE NULLIF(device_type, 0)
                END AS device_type,
                CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
                    WHEN device_os ILIKE '%%unknown%%' THEN NULL
                    WHEN device_os ILIKE 'Android%%' THEN 'Android'
                    WHEN device_os ILIKE 'iOS%%' THEN 'iOS'
                    WHEN device_os ILIKE 'WinPhone%%' THEN 'WinPhone'
                    WHEN device_os ILIKE 'WinRT%%' THEN 'WinRT'
                    WHEN device_os ILIKE 'Windows%%' THEN 'Windows'
                    WHEN device_os ILIKE 'MacOSX%%' THEN 'macOS'
                    WHEN device_os ILIKE 'macOS%%' THEN 'macOS'
                    WHEN device_os IN ('Linux', 'Ubuntu', 'Debian', 'Fedora') THEN 'Linux'
                    WHEN device_os ILIKE 'ChromeOS' THEN 'ChromeOS'
                    WHEN NULLIF(TRIM(device_os), '') IS NOT NULL THEN 'Other'
                    ELSE NULL
                END AS device_os,
                CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
                    WHEN device_os_version ILIKE '%%unknown%%' THEN NULL
                    WHEN device_os_version ILIKE 'Android%%' THEN device_os_version
                    WHEN device_os_version ILIKE 'iOS%%' THEN REPLACE(device_os_version, ';', '')  -- some special case
                    WHEN device_os_version ILIKE 'WinPhone%%' THEN device_os_version
                    WHEN device_os_version ILIKE 'WinRT%%' THEN device_os_version
                    WHEN device_os_version ILIKE 'Windows%%' THEN device_os_version
                    WHEN device_os_version ILIKE 'MacOS%%' THEN device_os_version
                    WHEN device_os_version ILIKE 'ChromeOS%%' THEN device_os_version
                    WHEN NULLIF(TRIM(device_os_version), '') IS NOT NULL THEN 'Other'
                    ELSE NULL
                END AS device_os_version,

                CASE WHEN browser = 'ucBrowser' THEN 'UC_BROWSER'
                    ELSE NULLIF(TRIM(UPPER(browser)), '')
                END as browser,

                CASE WHEN connection_type IN ('cableDSL', 'corporate', 'dialup') THEN 'wifi'
                    WHEN connection_type = 'cellular' THEN 'cellular'
                    ELSE NULL
                END as connection_type,

                CASE WHEN environment IN (
                        {% for environment in valid_environments %}
                            {% if forloop.last %}
                                '{{ environment }}'
                            {% else %}
                                '{{ environment }}',
                            {% endif %}
                        {% endfor %}
                    ) THEN environment
                    ELSE NULL
                END as environment,

                NULLIF(zem_placement_type, 0) as zem_placement_type,
                NULLIF(video_playback_method, 0) as video_playback_method,

                NULLIF(TRIM(UPPER(country)), '') AS country,
                CASE WHEN state ILIKE '%%-%%' THEN NULLIF(TRIM(UPPER(state)), '')
                    ELSE NULLIF(TRIM(UPPER(country)), '') || '-' || NULLIF(TRIM(UPPER(state)), '')
                END AS state,
                CASE WHEN country ILIKE 'US' AND dma BETWEEN 500 AND 882 THEN dma
                    ELSE NULL
                END AS dma,
                NULLIF(city_id, 0) AS city_id,

                NULLIF(TRIM(LOWER(age)), '') as age,
                NULLIF(TRIM(LOWER(gender)), '') as gender,
                NULLIF(TRIM(LOWER(age)), '') || ' ' || COALESCE(TRIM(LOWER(gender)), '') AS age_gender,

                outbrain_publisher_id,
                outbrain_section_id,

                SUM(impressions) as impressions,
                SUM(clicks) as clicks,
                SUM(spend) as spend,
                SUM(data_spend) as data_spend,
                SUM(video_start) as video_start,
                SUM(video_first_quartile) as video_first_quartile,
                SUM(video_midpoint) as video_midpoint,
                SUM(video_third_quartile) as video_third_quartile,
                SUM(video_complete) as video_complete,
                SUM(video_progress_3s) as video_progress_3s,
                SUM(mrc50_measurable) as mrc50_measurable,
                SUM(mrc50_viewable) as mrc50_viewable,
                SUM(mrc100_measurable) as mrc100_measurable,
                SUM(mrc100_viewable) as mrc100_viewable,
                SUM(vast4_measurable) as vast4_measurable,
                SUM(vast4_viewable) as vast4_viewable,
                SUM(ssp_spend) as ssp_spend
            FROM (SELECT * FROM stats_diff UNION ALL SELECT * FROM stats) AS stats
            WHERE
                ((hour is null and date=%(date)s)
                OR (hour IS NOT NULL AND (
                    (date=%(tzdate_from)s AND hour >= %(tzhour_from)s)
                    OR (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
                )))
                {% if account_id %}
                    AND ad_group_id=ANY(%(ad_group_id)s)
                {% endif %}
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
        ) a
        left outer join mvh_source b on a.source_slug=b.bidder_slug
        join mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id
        join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
        join mvh_currency_exchange_rates cer on c.account_id=cer.account_id and a.date=cer.date
    WHERE
        a.date=%(date)s
    {% if account_id %}
        AND c.account_id=%(account_id)s
    {% endif %}
);

{% endautoescape %}
