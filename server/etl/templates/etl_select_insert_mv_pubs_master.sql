INSERT INTO mv_pubs_master(
    SELECT
        date,
        source_id,

        agency_id,
        account_id,
        campaign_id,
        ad_group_id,
        publisher,
        NULL,

        device_type,
        country,
        state,
        dma,
        age,
        gender,
        age_gender,

        SUM(impressions) as impressions,  -- we don't have impressions for outbrain by publishers
        -- copy everything but outbrain stats
        SUM(CASE WHEN source_id<>3 THEN clicks ELSE 0 END) as clicks,
        SUM(CASE WHEN source_id<>3 THEN cost_nano ELSE 0 END) as cost_nano,
        SUM(CASE WHEN source_id<>3 THEN data_cost_nano ELSE 0 END) as data_cost_nano,

        -- keep postclicks
        SUM(visits) as visits,
        SUM(new_visits) as new_visits,
        SUM(bounced_visits) as bounced_visits,
        SUM(pageviews) as pageviews,
        SUM(total_time_on_site) as total_time_on_site,

        SUM(CASE WHEN source_id<>3 THEN effective_cost_nano ELSE 0 END) as effective_cost_nano,
        SUM(CASE WHEN source_id<>3 THEN effective_data_cost_nano ELSE 0 END) as effective_data_cost_nano,
        SUM(CASE WHEN source_id<>3 THEN license_fee_nano ELSE 0 END) as license_fee_nano,
        SUM(CASE WHEN source_id<>3 THEN margin_nano ELSE 0 END) as margin_nano,

        SUM(users) as users,
        SUM(returning_users) as returning_users

    FROM mv_master
    WHERE date BETWEEN %(date_from)s AND %(date_to)s AND publisher IS NOT NULL AND publisher <> ''
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15
)