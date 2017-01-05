{% load backtosql_tags %}
{% autoescape off %}

SELECT
    publisher
FROM
    mv_pubs_ad_group
WHERE
    ad_group_id = %s
GROUP BY
    publisher
HAVING
    sum(clicks) > 0
ORDER BY
    sum(clicks) DESC
LIMIT 15

{% endautoescape %}
