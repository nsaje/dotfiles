{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ breakdown|column_as_alias }},
    {{ aggregates|column_as_alias }}
FROM
    stats
WHERE
    (date=%(date)s AND hour IS NULL)
    OR
    (hour IS NOT NULL AND (
        (date=%(tzdate_from)s AND hour >= %(tzhour_from)s) OR
        (date=%(tzdate_to)s AND hour < %(tzhour_to)s)
    ))
GROUP BY
    {{ breakdown|only_alias }};

{% endautoescape %}