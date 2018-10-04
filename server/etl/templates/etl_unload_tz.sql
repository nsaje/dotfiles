{% autoescape off %}

UNLOAD
('SELECT * FROM {{ table }} WHERE (date BETWEEN \'{{ tzdate_from }}\' AND \'{{ tzdate_to }}\') AND ((hour is null and date >= \'{{ date_from }}\' and date <= \'{{ date_to }}\') OR (hour is not null and date > \'{{ tzdate_from }}\' and date < \'{{ tzdate_to }}\') OR (hour is not null and ((date=\'{{tzdate_from}}\' and hour >= {{ tzhour_from }}) or (date = \'{{tzdate_to}}\' and hour < {{tzhour_to}})))) {% if account_id_str %} AND ad_group_id IN ({{ ad_group_id|join:"," }}){% endif %}')
TO %(s3_url)s
DELIMITER AS %(delimiter)s
CREDENTIALS %(credentials)s
ADDQUOTES
ESCAPE
NULL AS '$NA$'
GZIP
MANIFEST
;

{% endautoescape %}
