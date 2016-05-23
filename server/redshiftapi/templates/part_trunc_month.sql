{% load backtosql_tags %}
DATE_TRUNC('month', {{ p }}{{ column_name }}) {{ alias|as_kw }}