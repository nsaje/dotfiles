{% load backtosql_tags %}
{% autoescape off %}

SELECT
    zuid,
    slug,
    date,
    conversion_id,
    conversion_timestamp,
    account_id,
    campaign_id,
    ad_group_id,
    content_ad_id,
    source_id,
    touchpoint_id,
    touchpoint_timestamp,
    conversion_lag,
    publisher
FROM conversions
WHERE
    date=%(date)s
    {% if account_id %}
        AND account_id=%(account_id)s
    {% endif %}

{% endautoescape %}