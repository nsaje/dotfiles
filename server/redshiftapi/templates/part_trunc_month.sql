{% load backtosql_tags %}
DATE_TRUNC('month', {{ p }}{{ column_name }}))::date {{ alias|as_kw }}
