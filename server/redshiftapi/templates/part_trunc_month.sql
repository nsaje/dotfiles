{% load backtosql_tags %}
TRUNC(DATE_TRUNC('month', {{ p }}{{ column_name }})) {{ alias|as_kw }}