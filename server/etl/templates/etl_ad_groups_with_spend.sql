
 SELECT ad_group_id
 FROM stats
 WHERE
  -- query only date first so redshift can use sort key
  date >= %(tzdate_from)s AND date <= %(tzdate_to)s AND (
    (hour is null and date>=%(date_from)s AND date<=%(date_to)s)
    OR
    (hour is not null and date>%(tzdate_from)s AND date<%(tzdate_to)s)
    OR
    (hour IS NOT NULL AND (
      (date=%(tzdate_from)s AND hour >= %(tzhour_from)s) OR
      (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
    ))
  )
 GROUP BY ad_group_id
 HAVING sum(spend) > 0 or sum(data_spend) > 0
