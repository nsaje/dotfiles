{% load backtosql_tags %}
{% autoescape off %}

SELECT
    country,
    state,
    sum(impressions) as impressions
FROM
    mv_content_ad_delivery_geo
WHERE
    content_ad_id = %s
GROUP BY
    country,
    state
ORDER BY
    sum(impressions) DESC

{% endautoescape %}
