--- K3E

SELECT
{{ breakdown|g_alias:"t" }},
{{ aggregates|g_alias:"t" }}
FROM (
SELECT
{{ breakdown|g_w_alias:"tt" }},
{{ aggregates|g_w_alias:"tt" }}
ROW_NUMBER() OVER (PARTITION BY {{ breakdown|slice:":-1"|g_alias:"tt" }}, ORDER BY {{ aggregates|first|g_alias }}) rn
FROM {{ view }} tt
WHERE
tt.ad_group_id=%(ad_group)s AND
tt.dt >= %(date_from)s AND tt.dt <= %(date_to)s
{% for k,v in constraints.items %}
tt.{{ k }}=%({{k}})s
{% endfor %}
GROUP BY {{ breakdown|indices }}
) t
WHERE t.rn <= {{ group_size }}
ORDER BY {{ breakdown|g_alias:"t" }}
LIMIT {{ total_size }};