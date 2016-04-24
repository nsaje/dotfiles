CASE WHEN MAX({{ p }}visits) IS NULL AND
       MAX({{ p }}pageviews) IS NULL AND
       MAX({{ p }}new_visits) IS NULL AND
       MAX({{ p }}bounced_visits) IS NULL AND
       MAX({{ p }}total_time_on_site) IS NULL
     THEN 0 ELSE 1
END {{ alias }}