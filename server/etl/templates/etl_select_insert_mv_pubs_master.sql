INSERT INTO mv_master_pubs(
    SELECT
        date,
        source_id,

        account_id,
        campaign_id,
        ad_group_id,
        publisher,
        publisher_source_id,
        NULL,

        device_type,
        device_os,
        device_os_version,
        environment,

        zem_placement_type,
        video_playback_method,

        country,
        state,
        dma,
        city_id,

        age,
        gender,
        age_gender,

        SUM(impressions) as impressions,
        SUM(clicks) as clicks,
        SUM(cost_nano) as cost_nano,
        SUM(data_cost_nano) as data_cost_nano,

        SUM(visits) as visits,
        SUM(new_visits) as new_visits,
        SUM(bounced_visits) as bounced_visits,
        SUM(pageviews) as pageviews,
        SUM(total_time_on_site) as total_time_on_site,

        SUM(effective_cost_nano) as effective_cost_nano,
        SUM(effective_data_cost_nano) as effective_data_cost_nano,
        SUM(license_fee_nano) as license_fee_nano,
        SUM(margin_nano) as margin_nano,

        SUM(users) as users,
        SUM(returning_users) as returning_users,

        SUM(video_start) as video_start,
        SUM(video_first_quartile) as video_first_quartile,
        SUM(video_midpoint) as video_midpoint,
        SUM(video_third_quartile) as video_third_quartile,
        SUM(video_complete) as video_complete,
        SUM(video_progress_3s) as video_progress_3s,

        SUM(local_cost_nano) as local_cost_nano,
        SUM(local_data_cost_nano) as local_data_cost_nano,
        SUM(local_effective_cost_nano) as local_effective_cost_nano,
        SUM(local_effective_data_cost_nano) as local_effective_data_cost_nano,
        SUM(local_license_fee_nano) as local_license_fee_nano,
        SUM(local_margin_nano) as local_margin_nano,

        SUM(mrc50_measurable) as mrc50_measurable,
        SUM(mrc50_viewable) as mrc50_viewable,
        SUM(mrc100_measurable) as mrc100_measurable,
        SUM(mrc100_viewable) as mrc100_viewable,
        SUM(vast4_measurable) as vast4_measurable,
        SUM(vast4_viewable) as vast4_viewable,

        SUM(ssp_cost_nano) as ssp_cost_nano,
        SUM(local_ssp_cost_nano) as local_ssp_cost_nano,

        SUM(base_effective_cost_nano) as base_effective_cost_nano,
        SUM(base_effective_data_cost_nano) as base_effective_data_cost_nano,
        SUM(service_fee_nano) as service_fee_nano,

        SUM(local_base_effective_cost_nano) as local_base_effective_cost_nano,
        SUM(local_base_effective_data_cost_nano) as local_base_effective_data_cost_nano,
        SUM(local_service_fee_nano) as local_service_fee_nano
    FROM mv_master
    WHERE date BETWEEN %(date_from)s AND %(date_to)s AND publisher IS NOT NULL AND source_id <> 3
          {% if account_id %}
              AND account_id=%(account_id)s
          {% endif %}
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21
)
