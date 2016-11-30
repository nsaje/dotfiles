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
      LOWER(publisher),

      -- check dash/constants.py DeviceType for correct setting.
      -- OpenRTB values:
      -- 1 | Mobile/Tablet
      -- 2 | Personal Computer
      -- 3 | Connected TV
      -- 4 | Phone
      -- 5 | Tablet
      -- 6 | Connected Device
      -- 7 | Set Top Box
      CASE
          WHEN device_type = 4 THEN 3 -- mobile
          WHEN device_type = 2 THEN 1 -- desktop
          WHEN device_type = 5 THEN 2 -- tablet
          ELSE 0 -- undefined
      END as device_type,
      UPPER(TRIM(country)) AS country,
      UPPER(TRIM(state)) AS state,
      dma,
      CASE WHEN TRIM(age)='18-20' THEN 1
           WHEN TRIM(age)='21-29' THEN 2
           WHEN TRIM(age)='30-39' THEN 3
           WHEN TRIM(age)='40-49' THEN 4
           WHEN TRIM(age)='50-64' THEN 5
           WHEN TRIM(age)='65+'   THEN 6
           ELSE 0
      END AS age,
      CASE WHEN TRIM(LOWER(gender))='male'   THEN 1
           WHEN TRIM(LOWER(gender))='female' THEN 2
           ELSE 0
      END AS gender,
      CASE
          WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='18-20' THEN 1
          WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='18-20' THEN 2
          WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='18-20' THEN 3
          WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='21-29' THEN 4
          WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='21-29' THEN 5
          WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='21-29' THEN 6
          WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='30-39' THEN 7
          WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='30-39' THEN 8
          WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='30-39' THEN 9
          WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='40-49' THEN 10
          WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='40-49' THEN 11
          WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='40-49' THEN 12
          WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='50-64' THEN 13
          WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='50-64' THEN 14
          WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='50-64' THEN 15
          WHEN TRIM(LOWER(gender))='male'                    AND TRIM(age)='65+'   THEN 16
          WHEN TRIM(LOWER(gender))='female'                  AND TRIM(age)='65+'   THEN 17
          WHEN TRIM(LOWER(gender)) NOT IN ('male', 'female') AND TRIM(age)='65+'   THEN 18
      ELSE 0
      END AS age_gender,

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

      {% if account_id %}
          AND ad_group_id=ANY(%(ad_group_id)s)
      {% endif %}
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
);