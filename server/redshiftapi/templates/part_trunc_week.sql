-- TODO note this is monday-based, not start_date based
{% load backtosql_tags %}
TRUNC(DATE_TRUNC('week', {{ p }}{{ column_name }})) {{ alias|as_kw }}