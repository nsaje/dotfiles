{% autoescape off %}

COPY {{ table }}
FROM %(s3_url)s

{% if format %}
FORMAT {{ format|upper }} {% if format != "csv" %}'auto'{% endif %}
{% endif %}

{% if not format or format == "csv" %}
DELIMITER AS %(delimiter)s
BLANKSASNULL EMPTYASNULL
{% if removequotes %}REMOVEQUOTES{% endif %}
{% if escape %}ESCAPE{% endif %}
{% if null_as %}NULL AS '{{ null_as }}'{% endif %}
{% endif %}

CREDENTIALS %(credentials)s
MAXERROR {{ maxerror }}
{% if gzip %}GZIP{% endif %}
{% if is_manifest %}MANIFEST{% endif %}
{% if truncate_columns %}TRUNCATECOLUMNS{% endif %}
;

{% endautoescape %}
