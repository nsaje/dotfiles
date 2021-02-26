{% autoescape off %}

INSERT INTO mv_adgroup_placement (
    SELECT
        a.date,

        c.account_id,
        c.campaign_id,
        c.ad_group_id,

        CASE WHEN a.date < '2020-01-01' THEN b.parent_source_id --Date will be changed when merged
            ELSE b.source_id
        END as source_id,

        a.publisher,
        COALESCE(a.publisher, '') || '__' || b.source_id as publisher_source_id,
        a.placement_type,
        a.placement,

        a.impressions as impressions,
        a.clicks as clicks,
        -- convert micro to nano
        a.spend::bigint * 1000 as cost_nano,
        a.data_spend::bigint * 1000 as data_cost_nano,

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

        null as visits,
        null as new_visits,
        null as bounced_visits,
        null as pageviews,
        null as total_time_on_site,
        null as users,
        null as returning_users,

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
        a.outbrain_publisher_id,
        a.outbrain_section_id,
        b.source_id as original_source_id
    FROM
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
                CASE WHEN TRIM(placement)='' THEN NULL ELSE translate(placement, chr(0), '') END AS placement,

                outbrain_publisher_id,
                outbrain_section_id,

                SUM(impressions) AS impressions,
                SUM(clicks) AS clicks,
                SUM(spend) AS spend,
                SUM(data_spend) AS data_spend,

                SUM(video_start) AS video_start,
                SUM(video_first_quartile) AS video_first_quartile,
                SUM(video_midpoint) AS video_midpoint,
                SUM(video_third_quartile) AS video_third_quartile,
                SUM(video_complete) AS video_complete,
                SUM(video_progress_3s) AS video_progress_3s,

                SUM(mrc50_measurable) as mrc50_measurable,
                SUM(mrc50_viewable) as mrc50_viewable,
                SUM(mrc100_measurable) as mrc100_measurable,
                SUM(mrc100_viewable) as mrc100_viewable,
                SUM(vast4_measurable) as vast4_measurable,
                SUM(vast4_viewable) as vast4_viewable,

                SUM(ssp_spend) as ssp_spend
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
                1, 2, 3, 4, 5, 6, 7, 8
        ) a
        LEFT OUTER JOIN mvh_source b ON a.source_slug=b.bidder_slug
        JOIN mvh_adgroup_structure c on a.ad_group_id=c.ad_group_id
        JOIN mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and a.date=cf.date
        JOIN mvh_currency_exchange_rates cer on c.account_id=cer.account_id and a.date=cer.date
    WHERE
        a.date BETWEEN %(date_from)s AND %(date_to)s
        {% if account_id %}
        AND c.account_id=%(account_id)s
        {% endif %}
);

{% endautoescape %}
