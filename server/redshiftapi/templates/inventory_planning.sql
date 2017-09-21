{% load backtosql_tags %}
{% autoescape off %}

SELECT

{% if breakdown %}
{{ breakdown|column_as_alias }},
{% endif %}

{{ aggregates|column_as_alias }}

FROM mv_inventory

{% if constraints %}
WHERE
{{ constraints|generate }}
{% endif %}

{% if breakdown %}
GROUP BY {{ breakdown|indices }}
{% endif %}

LIMIT 20000

{% endautoescape %}
