{% load backtosql_tags %}
{% autoescape off %}

SELECT
    state,
    sum(impressions) as impressions
FROM
    mv_contentad_geo
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
GROUP BY
    state
ORDER BY
    sum(impressions) DESC

{% endautoescape %}
