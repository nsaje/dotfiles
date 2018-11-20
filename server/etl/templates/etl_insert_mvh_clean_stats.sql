INSERT INTO mvh_clean_stats (
  SELECT
      CASE
          WHEN hour is null THEN date
          {% for date_context in date_ranges %}
          WHEN hour is not null AND (
              (date='{{ date_context.tzdate_from }}'::date AND hour >= {{ date_context.tzhour_from }}) OR
              (date='{{ date_context.tzdate_to }}'::date AND hour < {{ date_context.tzhour_to }})
          )
          THEN '{{ date_context.date }}'::date
          {% endfor %}
      END as date,
      stats.media_source as source_slug,

      ad_group_id,
      content_ad_id,
      -- no outbrain publishers here
      CASE
          WHEN media_source = '{{ yahoo_slug }}' THEN 'all publishers'
          ELSE LOWER(publisher)
      END as publisher,

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

      CASE WHEN placement_medium IN (
               {% for placement_medium in valid_placement_mediums %}
                   {% if forloop.last %}
                       '{{ placement_medium }}'
                   {% else %}
                       '{{ placement_medium }}',
                   {% endif %}
               {% endfor %}
           ) THEN placement_medium
           ELSE NULL
      END as placement_medium,

      NULLIF(placement_type, 0) as placement_type,
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

      SUM(impressions) as impressions,
      SUM(clicks) as clicks,
      SUM(spend) as spend,
      SUM(data_spend) as data_spend,
      SUM(video_start) as video_start,
      SUM(video_first_quartile) as video_first_quartile,
      SUM(video_midpoint) as video_midpoint,
      SUM(video_third_quartile) as video_third_quartile,
      SUM(video_complete) as video_complete,
      SUM(video_progress_3s) as video_progress_3s
  FROM (SELECT * FROM stats_diff UNION ALL SELECT * FROM stats) AS stats
  WHERE
      ((hour is null and date>=%(date_from)s AND date<=%(date_to)s)
      OR
      (hour is not null and date>%(tzdate_from)s AND date<%(tzdate_to)s)
      OR
      (hour IS NOT NULL AND (
          (date=%(tzdate_from)s AND hour >= %(tzhour_from)s) OR
          (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
      )))

      {% if account_id %}
          AND ad_group_id=ANY(%(ad_group_id)s)
      {% endif %}
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18
);
