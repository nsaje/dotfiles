{% autoescape off %}

COPY {{ table }}
FROM %(s3_url)s
FORMAT CSV
DELIMITER AS %(delimiter)s
CREDENTIALS %(credentials)s
MAXERROR 0 BLANKSASNULL EMPTYASNULL
{% if is_manifest %}MANIFEST{% endif %}
;

{% endautoescape %}
