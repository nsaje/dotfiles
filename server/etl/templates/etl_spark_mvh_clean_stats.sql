SELECT
  CASE
	  WHEN hour is null THEN date
	  {% for date_context in date_ranges %}
	  WHEN hour is not null AND (
		  (date='{{ date_context.tzdate_from }}' AND hour >= {{ date_context.tzhour_from }}) OR
		  (date='{{ date_context.tzdate_to }}' AND hour < {{ date_context.tzhour_to }})
	  )
	  THEN '{{ date_context.date }}'
	  {% endfor %}
  END as date,
  stats.media_source as source_slug,

  ad_group_id,
  content_ad_id,
  -- no outbrain publishers here
  CASE
	  WHEN media_source = '{{ yahoo_slug }}' THEN 'all publishers'
	  WHEN media_source = '{{ outbrain_slug }}' THEN NULL  -- special case for outbrain to avoid coalesce and spark bug
	  ELSE COALESCE(LOWER(publisher), '')  -- coalesce is here for spark bug treating empty values as null in input csv
  END as publisher,

  CASE WHEN device_type = 1 THEN 4  -- convert legacy OpenRTB `mobile` to `phone`
	   WHEN device_type = 6 THEN 3
	   WHEN device_type = 7 THEN 3
	   ELSE NULLIF(device_type, 0)
  END AS device_type,
  CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
	   WHEN LOWER(device_os) LIKE LOWER('%%unknown%%') THEN NULL
	   WHEN LOWER(device_os) LIKE LOWER('Android%%') THEN 'Android'
	   WHEN LOWER(device_os) LIKE LOWER('iOS%%') THEN 'iOS'
	   WHEN LOWER(device_os) LIKE LOWER('WinPhone%%') THEN 'WinPhone'
	   WHEN LOWER(device_os) LIKE LOWER('WinRT%%') THEN 'WinRT'
	   WHEN LOWER(device_os) LIKE LOWER('Windows%%') THEN 'Windows'
	   WHEN LOWER(device_os) LIKE LOWER('MacOSX%%') THEN 'macOS'
	   WHEN LOWER(device_os) LIKE LOWER('macOS%%') THEN 'macOS'
	   WHEN device_os IN ('Linux', 'Ubuntu', 'Debian', 'Fedora') THEN 'Linux'
	   WHEN LOWER(device_os) LIKE LOWER('ChromeOS') THEN 'ChromeOS'
	   WHEN NULLIF(TRIM(device_os), '') IS NOT NULL THEN 'Other'
	   ELSE NULL
  END AS device_os,
  CASE WHEN date < '2017-05-01' THEN NULL  -- before that input was not sanitized
	   WHEN LOWER(device_os_version) LIKE LOWER('%%unknown%%') THEN NULL
	   WHEN LOWER(device_os_version) LIKE LOWER('Android%%') THEN device_os_version
	   WHEN LOWER(device_os_version) LIKE LOWER('iOS%%') THEN REPLACE(device_os_version, ';', '')  -- some special case
	   WHEN LOWER(device_os_version) LIKE LOWER('WinPhone%%') THEN device_os_version
	   WHEN LOWER(device_os_version) LIKE LOWER('WinRT%%') THEN device_os_version
	   WHEN LOWER(device_os_version) LIKE LOWER('Windows%%') THEN device_os_version
	   WHEN LOWER(device_os_version) LIKE LOWER('MacOS%%') THEN device_os_version
	   WHEN LOWER(device_os_version) LIKE LOWER('ChromeOS%%') THEN device_os_version
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
  CASE WHEN state LIKE '%%-%%' THEN NULLIF(TRIM(UPPER(state)), '')
	   ELSE NULLIF(TRIM(UPPER(country)), '') || '-' || NULLIF(TRIM(UPPER(state)), '')
  END AS state,
  CASE WHEN country LIKE 'US' AND dma BETWEEN 500 AND 882 THEN dma
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
FROM stats
WHERE
  ((hour is null and date>='{{ date_from }}' AND date<='{{ date_to }}')
  OR
  (hour is not null and date>'{{ tzdate_from }}' AND date<'{{ tzdate_to }}')
  OR
  (hour IS NOT NULL AND (
	  (date='{{ tzdate_from }}' AND hour >= '{{ tzhour_from }}') OR
	  (date='{{ tzdate_to }}' AND hour < '{{ tzhour_to }}')
  )))

  {% if account_id %}
	  AND ad_group_id IN ({{ ad_group_id|join:"," }})
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18
ORDER BY 1, 2, 3, 4, 5
