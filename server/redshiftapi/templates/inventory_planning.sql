{% load backtosql_tags %}
{% autoescape off %}

SELECT

{% if breakdown %}
{{ breakdown|only_column }},
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

{% endautoescape %}
