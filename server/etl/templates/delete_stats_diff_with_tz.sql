{% autoescape off %}

DELETE FROM {{ table_name }}
WHERE ({{ table_name }}.date BETWEEN '{{ tzdate_from }}' AND '{{ tzdate_to }}')
AND (
    ({{ table_name }}.hour IS NULL AND {{ table_name }}.date >= '{{ date_from }}' AND {{ table_name }}.date <= '{{ date_to }}')
    OR ({{ table_name }}.hour IS NOT NULL AND {{ table_name }}.date > '{{ tzdate_from }}' AND {{ table_name }}.date < '{{ tzdate_to }}')
    OR ( {{ table_name }}.hour IS NOT NULL AND (
      ({{ table_name }}.date='{{ tzdate_from }}' AND {{ table_name }}.hour >= '{{ tzhour_from }}')
      OR ({{ table_name }}.date = '{{ tzdate_to }}' AND {{ table_name }}.hour < '{{ tzhour_to }}')
    )
  )
)
;

{% endautoescape %}