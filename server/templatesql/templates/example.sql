{% load query_helpers %}
SELECT
 {{ breakdowns|prefix:"a"|join:"," }},
 {{ aggregates|prefix:"a"|join:"," }}
FROM {{ view }} a
WHERE
 a.user_id=ANY(%(user_id)s) AND
 a.date>=%(date_from)s AND a.date<=%(date_to)s
GROUP BY 1;
