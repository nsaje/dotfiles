{% autoescape off %}

DELETE FROM {{ table }}
WHERE date BETWEEN %(date_from)s AND %(date_to)s;

{% endautoescape %}