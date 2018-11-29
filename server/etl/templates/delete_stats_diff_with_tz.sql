{% autoescape off %}

DELETE FROM stats_diff
WHERE (stats_diff.date BETWEEN '{{ tzdate_from }}' AND '{{ tzdate_to }}')
AND (
    (stats_diff.hour IS NULL AND stats_diff.date >= '{{ date_from }}' AND stats_diff.date <= '{{ date_to }}')
    OR (stats_diff.hour IS NOT NULL AND stats_diff.date > '{{ tzdate_from }}' AND stats_diff.date < '{{ tzdate_to }}')
    OR ( stats_diff.hour IS NOT NULL AND (
      (stats_diff.date='{{ tzdate_from }}' AND stats_diff.hour >= '{{ tzhour_from }}')
      OR (stats_diff.date = '{{ tzdate_to }}' AND stats_diff.hour < '{{ tzhour_to }}')
    )
  )
)
;

{% endautoescape %}