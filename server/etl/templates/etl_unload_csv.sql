{% autoescape off %}

UNLOAD
('SELECT * FROM {{ table }} WHERE (date BETWEEN \'{{ date_from_str }}\' AND \'{{ date_to_str }}\') {% if account_id_str %} AND account_id = {{ account_id_str }}{% endif %}')
TO %(s3_url)s
DELIMITER AS %(delimiter)s
CREDENTIALS %(credentials)s
ADDQUOTES
ESCAPE
;

{% endautoescape %}
