{% load backtosql_tags %}
{% autoescape off %}

SELECT
    sum(clicks) as clicks,
    sum(impressions) as impressions,
    {{ ctr|only_column }} as ctr
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
