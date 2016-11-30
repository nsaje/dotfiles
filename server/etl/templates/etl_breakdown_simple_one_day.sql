{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ breakdown|column_as_alias }},
    {{ aggregates|column_as_alias }}
FROM
    {{ table }}
WHERE
    date=%(date)s
    {% if account_id %}
        AND ad_group_id=ANY(%(ad_group_id)s)
    {% endif %}
GROUP BY
    {{ breakdown|only_alias }};

{% endautoescape %}