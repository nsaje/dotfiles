{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ cost|only_column }} as cost
FROM
    mv_contentad
WHERE
    content_ad_id IN (
        {% for content_ad_id in content_ad_ids %}
            {% if forloop.last %}
                {{ content_ad_id }}
            {% else %}
                {{ content_ad_id }},
            {% endif %}
        {% endfor %}
    )

{% endautoescape %}
