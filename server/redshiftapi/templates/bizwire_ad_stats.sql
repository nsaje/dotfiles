{% load backtosql_tags %}
{% autoescape off %}

SELECT
    sum(clicks) as clicks,
    sum(impressions) as impressions,
    {{ ctr|only_column }} as ctr
FROM
    mv_content_ad
WHERE
    content_ad_id = %s

{% endautoescape %}
