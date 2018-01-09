{% autoescape off %}

COPY {{ table }}
FROM %(s3_url)s
{% if format_csv %}FORMAT CSV{% endif %}
DELIMITER AS %(delimiter)s
CREDENTIALS %(credentials)s
MAXERROR 0 BLANKSASNULL EMPTYASNULL
{% if removequotes %}REMOVEQUOTES{% endif %}
{% if escape %}ESCAPE{% endif %}
{% if null_as %}NULL AS '{{ null_as }}'{% endif %}
{% if gzip %}GZIP{% endif %}
{% if is_manifest %}MANIFEST{% endif %}
;

{% endautoescape %}
