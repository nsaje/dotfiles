-- TODO note this is monday-based, not start_date based
{% load backtosql_tags %}
DATE_TRUNC('week', {{ p }}{{ column_name }})::date {{ alias|as_kw }}
