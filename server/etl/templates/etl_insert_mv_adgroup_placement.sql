{% autoescape off %}

INSERT INTO mv_adgroup_placement (
    SELECT
        d.date,

        c.account_id,
        c.campaign_id,
        c.ad_group_id,

        d.source_id,
        d.publisher,
        COALESCE(d.publisher, '') || '__' || d.source_id as publisher_source_id,
        d.placement_type,
        d.placement,

        d.impressions as impressions,
        d.clicks as clicks,
        -- convert micro to nano
        d.spend::bigint * 1000 as cost_nano,
        d.data_spend::bigint * 1000 as data_cost_nano,

        round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_cost_nano,
        round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as effective_data_cost_nano,
        round(
            (
                (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
            ) * cf.pct_license_fee::decimal(10, 8) * 1000
        ) as license_fee_nano,
        round(
            (
                (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                (
                    (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                    (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                ) * cf.pct_license_fee::decimal(10, 8)
            ) * cf.pct_margin::decimal(10, 8) * 1000
        ) as margin_nano,

        d.video_start as video_start,
        d.video_first_quartile as video_first_quartile,
        d.video_midpoint as video_midpoint,
        d.video_third_quartile as video_third_quartile,
        d.video_complete as video_complete,
        d.video_progress_3s as video_progress_3s,

        round(d.spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_cost_nano,
        round(d.data_spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_data_cost_nano,
        -- casting intermediate values to bigint (decimal(19, 0)) because of max precision of 38 in DB
        round(round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000)::bigint * cer.exchange_rate::decimal(10, 4)) as local_effective_cost_nano,
        round(round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000)::bigint * cer.exchange_rate::decimal(10, 4)) as local_effective_data_cost_nano,
        round(
            round(
                (
                    (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                    (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                ) * cf.pct_license_fee::decimal(10, 8) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_license_fee_nano,
        round(
            round(
                (
                    (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                    (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                    (
                        (nvl(d.spend, 0) * cf.pct_actual_spend::decimal(10, 8)) +
                        (nvl(d.data_spend, 0) * cf.pct_actual_spend::decimal(10, 8))
                    ) * cf.pct_license_fee::decimal(10, 8)
                ) * cf.pct_margin::decimal(10, 8) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_margin_nano,

        null as visits,
        null as new_visits,
        null as bounced_visits,
        null as pageviews,
        null as total_time_on_site,
        null as users,
        null as returning_users
    FROM
        (
            (
                SELECT
                    CASE
                        WHEN hour IS NULL THEN date
                        {% for date_context in date_ranges %}
                        WHEN hour IS NOT NULL AND (
                            (date='{{ date_context.tzdate_from }}'::date AND hour >= {{ date_context.tzhour_from }})
                            OR (date='{{ date_context.tzdate_to }}'::date AND hour < {{ date_context.tzhour_to }})
                        )
                        THEN '{{ date_context.date }}'::date
                        {% endfor %}
                    END AS date,
                    stats_placement.media_source AS source_slug,

                    ad_group_id,
                    LOWER(publisher) AS publisher,
                    NULLIF(placement_type, 0) AS placement_type,
                    LOWER(placement) AS placement,
                    
                    SUM(impressions) AS impressions,
                    SUM(clicks) AS clicks,
                    SUM(spend) AS spend,
                    SUM(data_spend) AS data_spend,

                    SUM(video_start) AS video_start,
                    SUM(video_first_quartile) AS video_first_quartile,
                    SUM(video_midpoint) AS video_midpoint,
                    SUM(video_third_quartile) AS video_third_quartile,
                    SUM(video_complete) AS video_complete,
                    SUM(video_progress_3s) AS video_progress_3s
                FROM (SELECT * from stats_placement_diff UNION ALL SELECT * FROM stats_placement) AS stats_placement
                WHERE
                    ((hour IS NULL AND date>=%(date_from)s AND date<=%(date_to)s)
                    OR (hour IS NOT NULL and date>%(tzdate_from)s AND date<%(tzdate_to)s)
                    OR (hour IS NOT NULL AND (
                        (date=%(tzdate_from)s AND hour >= %(tzhour_from)s)
                        OR (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
                    )))

                    {% if account_id %}
                    AND ad_group_id=ANY(%(ad_group_id)s)
                    {% endif %}
                GROUP BY
                    1, 2, 3, 4, 5, 6
            ) a
            LEFT OUTER JOIN mvh_source b
            ON a.source_slug=b.bidder_slug
        ) d
        JOIN mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
        JOIN mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
        JOIN mvh_currency_exchange_rates cer on c.account_id=cer.account_id and d.date=cer.date
    WHERE
        d.date BETWEEN %(date_from)s AND %(date_to)s
        {% if account_id %}
        AND c.account_id=%(account_id)s
        {% endif %}
);

{% endautoescape %}
