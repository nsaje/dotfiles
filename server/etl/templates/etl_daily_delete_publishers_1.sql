{% autoescape off %}

DELETE FROM {{ table }}
WHERE date=%(date)s
    {% if account_id %}
    AND adgroup_id=ANY(%(ad_group_id)s)
    {% endif %}

{% endautoescape %}