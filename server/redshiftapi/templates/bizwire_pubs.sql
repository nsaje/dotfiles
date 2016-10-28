{% load backtosql_tags %}
{% autoescape off %}

SELECT
    publisher
FROM
    mv_pubs_master
WHERE
    content_ad_id = %s
GROUP BY
    publisher
HAVING
    sum(clicks) > 0

{% endautoescape %}
