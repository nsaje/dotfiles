SELECT
    date,
    source_id,

    account_id,
    campaign_id,
    ad_group_id,
    publisher,
    publisher_source_id,
    NULL AS external_id,

    device_type,
    device_os,
    device_os_version,
    placement_medium,

    placement_type,
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
    SUM(local_margin_nano) as local_margin_nano
FROM mv_master
WHERE date BETWEEN '{{ date_from }}' AND '{{ date_to }}' AND publisher IS NOT NULL AND source_id <> 3
      {% if account_id %}
          AND account_id={{ account_id }}
      {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21
