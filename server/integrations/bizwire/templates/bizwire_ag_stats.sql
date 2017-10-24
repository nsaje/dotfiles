{% load backtosql_tags %}
{% autoescape off %}

SELECT
    {{ industry_ctr|only_column }} as industry_ctr
FROM
    mv_adgroup
WHERE
    ad_group_id = %s

{% endautoescape %}
