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
      stats.media_source,
      ad_group_id,
      content_ad_id,
      publisher,

      extract_device_type(device_type) as device_type,
      extract_country(country) as country,
      extract_state(state) as state,
      extract_dma(dma) as dma,
      extract_age(age) as age,
      extract_gender(gender) as gender,
      extract_age_gender(stats.age, stats.gender) as age_gender,

      SUM(impressions) as impressions,
      SUM(clicks) as clicks,
      SUM(spend) as spend,
      SUM(data_spend) as data_spend
  FROM stats
  WHERE
      (hour is null and date>=%(date_from)s AND date<=%(date_to)s)
      OR
      (hour is not null and date>%(tzdate_from)s AND date<%(tzdate_to)s)
      OR
      (hour IS NOT NULL AND (
          (date=%(tzdate_from)s AND hour >= %(tzhour_from)s) OR
          (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
      ))
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
);