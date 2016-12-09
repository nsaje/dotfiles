{% autoescape off %}

DELETE FROM {{ table }}
WHERE (date BETWEEN %(date_from)s AND %(date_to)s)
      {% if account_id %}
          AND account_id=%(account_id)s
      {% endif %}
      ;

{% endautoescape %}