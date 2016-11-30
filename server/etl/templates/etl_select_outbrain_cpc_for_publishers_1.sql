{% load backtosql_tags %}
{% autoescape off %}

SELECT
    ad_group_id,
    SUM(spend) as spend,
    SUM(clicks) as clicks
FROM stats
WHERE media_source=%(media_source_slug)s AND date=%(date)s
      {% if account_id %}
          AND ad_group_id=ANY(%(ad_group_id)s)
      {% endif %}
GROUP BY 1;

{% endautoescape %}