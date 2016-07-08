{% autoescape off %}

DELETE FROM {{ table }}
WHERE date=%(date)s

{% endautoescape %}