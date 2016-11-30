{% load backtosql_tags %}
{% autoescape off %}

SELECT
    ad_group_id,
    type,
    source,
    lower(publisher),
    SUM(visits) as visits,
    SUM(new_visits) as new_visits,
    SUM(bounced_visits) as bounced_visits,
    SUM(pageviews) as pageviews,
    SUM(total_time_on_site) as total_time_on_site,
    LISTAGG(conversions, '\n') as conversions,
    SUM(users) as users
FROM postclickstats
WHERE
      date=%(date)s
      {% if account_id %}
          AND ad_group_id=ANY(%(ad_group_id)s)
      {% endif %}
GROUP BY 1, 2, 3, 4;

{% endautoescape %}