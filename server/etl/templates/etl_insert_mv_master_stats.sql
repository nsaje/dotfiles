{% autoescape off %}

INSERT INTO mv_master (
    SELECT
        d.date,
        d.source_id,

        c.account_id,
        c.campaign_id,
        d.ad_group_id,
        d.content_ad_id,

        d.publisher,
        COALESCE(d.publisher, '') || '__' || d.source_id as publisher_source_id,

        -- When adding new breakdown dimensions, add them to natural full outer join with mv_touchpointconversions below
        -- too!
        d.device_type,
        d.device_os,
        d.device_os_version,
        d.environment,

        d.zem_placement_type,
        d.video_playback_method,

        d.country,
        d.state,
        d.dma,
        d.city_id,

        d.age as age,
        d.gender as gender,
        d.age_gender as age_gender,

        d.impressions as impressions,
        d.clicks as clicks,
        -- convert micro to nano
        d.spend::bigint * 1000 as cost_nano,
        d.data_spend::bigint * 1000 as data_cost_nano,

        null as visits,
        null as new_visits,
        null as bounced_visits,
        null as pageviews,
        null as total_time_on_site,

        round(
            (d.spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
        ) as effective_cost_nano,
        round(
            (d.data_spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
        ) as effective_data_cost_nano,
        round(
          round(
            (
              (nvl(d.spend, 0) + nvl(d.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
            ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
          )::bigint * cf.pct_license_fee::decimal(10, 8)
        ) as license_fee_nano,
        round(
          (
            round(
              (
                (nvl(d.spend, 0) + nvl(d.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
              ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
            )::bigint * (1 + cf.pct_license_fee::decimal(10, 8)) -- add license fee
          ) * cf.pct_margin::decimal(10, 8)
        ) as margin_nano,

        null as users,
        null as returning_users,

        d.video_start as video_start,
        d.video_first_quartile as video_first_quartile,
        d.video_midpoint as video_midpoint,
        d.video_third_quartile as video_third_quartile,
        d.video_complete as video_complete,
        d.video_progress_3s as video_progress_3s,

        round(d.spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_cost_nano,
        round(d.data_spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_data_cost_nano,
        -- casting intermediate values to bigint (decimal(19, 0)) because of max precision of 38 in DB
        round(
            round(
                (d.spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_effective_cost_nano,
        round(
            round(
                (d.data_spend * cf.pct_actual_spend::decimal(10, 8)) * (1 + cf.pct_service_fee::decimal(10, 8)) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_effective_data_cost_nano,
        round(
          (
            round(
              (
                (nvl(d.spend, 0) + nvl(d.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
              ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
            )::bigint * cf.pct_license_fee::decimal(10, 8)
          ) * cer.exchange_rate::decimal(10, 4)
        ) as local_license_fee_nano,
        round(
          (
            (
              round(
                (
                  (nvl(d.spend, 0) + nvl(d.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) * 1000 -- effective spend
                ) * (1 + cf.pct_service_fee::decimal(10, 8)) -- add service fee
              )::bigint * (1 + cf.pct_license_fee::decimal(10, 8)) -- add license fee
            ) * cf.pct_margin::decimal(10, 8)
          ) * cer.exchange_rate::decimal(10, 4)
        ) as local_margin_nano,

        d.mrc50_measurable as mrc50_measurable,
        d.mrc50_viewable as mrc50_viewable,
        d.mrc100_measurable as mrc100_measurable,
        d.mrc100_viewable as mrc100_viewable,
        d.vast4_measurable as vast4_measurable,
        d.vast4_viewable as vast4_viewable,

        d.ssp_spend::bigint * 1000 as ssp_cost_nano,
        round(d.ssp_spend::bigint * 1000 * cer.exchange_rate::decimal(10, 4)) as local_ssp_cost_nano,

        round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as base_effective_cost_nano,
        round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000) as base_effective_data_cost_nano,
        round(
            (
                (nvl(d.spend, 0) + nvl(d.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) -- effective spend
            ) * cf.pct_service_fee::decimal(10, 8) * 1000
        ) as service_fee_nano,

        round(
            round(d.spend * cf.pct_actual_spend::decimal(10, 8) * 1000)::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_base_effective_cost_nano,
        round(
            round(d.data_spend * cf.pct_actual_spend::decimal(10, 8) * 1000)::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_base_effective_data_cost_nano,
        round(
            round(
                (
                    (nvl(d.spend, 0) + nvl(d.data_spend, 0)) * cf.pct_actual_spend::decimal(10, 8) -- effective spend
                ) * cf.pct_service_fee::decimal(10, 8) * 1000
            )::bigint * cer.exchange_rate::decimal(10, 4)
        ) as local_service_fee_nano
    FROM
        (
            (mvh_clean_stats a left outer join mvh_source b on a.source_slug=b.bidder_slug)
            natural full outer join (
                SELECT
                date,
                source_id,
                ad_group_id,
                content_ad_id,
                device_type,
                device_os,
                device_os_version,
                environment,
                country,
                state,
                dma,
                CASE WHEN source_id = 3 THEN NULL ELSE publisher END AS publisher
                FROM mv_touchpointconversions
                WHERE date=%(date)s
                {% if account_id %}
                AND account_id=%(account_id)s
                {% endif %}
                GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
            ) tpc
        ) d
        join mvh_adgroup_structure c on d.ad_group_id=c.ad_group_id
        join mvh_campaign_factors cf on c.campaign_id=cf.campaign_id and d.date=cf.date
        join mvh_currency_exchange_rates cer on c.account_id=cer.account_id and d.date=cer.date
    WHERE
        d.date=%(date)s
    {% if account_id %}
        AND c.account_id=%(account_id)s
    {% endif %}
);

{% endautoescape %}
