{% load backtosql_tags %}
{% autoescape off %}

SELECT
    ad_group_id,
    media_source_type,
    media_source,
    publisher,
    SUM(impressions) as impressions,
    SUM(clicks) as clicks,
    SUM(spend) as spend,
    SUM(data_spend) as data_spend
FROM stats
WHERE
      (date=%(date)s and hour is null) or
      (
          hour is not null and (
               (date = %(tzdate_from)s and hour >= %(tzhour_from)s) or
               (date = %(tzdate_to)s   and hour <  %(tzhour_to)s)
          )
      )
      {% if account_id %}
          AND ad_group_id=ANY(%(ad_group_id)s)
      {% endif %}
GROUP BY 1, 2, 3, 4;

{% endautoescape %}