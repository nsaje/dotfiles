{% load backtosql_tags %}

SELECT
{{ columns|g_w_alias:"a" }}
FROM (
     SELECT
        {{ columns|g_w_alias:"b" }},
        ROW_NUMBER() OVER (PARTITION BY {{ partition|g:"b" }} ORDER BY {{ order|g }}) AS rn
     FROM
        some_table b
     WHERE
        status=%(status)s AND
        date BETWEEN %(date_from)s AND %(date_to)s
     GROUP BY
        {{ breakdown|g_alias }}
     ) a
WHERE a.rn <= %(group_limit)s
OFFSET %(offset)s
LIMIT %(limit)s
