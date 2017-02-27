{% load backtosql_tags %}
{% autoescape off %}

SELECT
     ad_group_id,
     publisher_id,
     publisher_name,
     clicks,
     impressions,
     spend
FROM outbrainpublisherstats
WHERE date=%(date)s
      {% if account_id %}
          AND ad_group_id=ANY(%(ad_group_id)s)
      {% endif %}

{% endautoescape %}
