{% autoescape off %}

DELETE FROM {{ table }}
WHERE date=%(date)s
      {% if account_id %}
          AND account_id=%(account_id)s
      {% endif %}

{% endautoescape %}