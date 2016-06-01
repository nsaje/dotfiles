{% load backtosql_tags %}
TRUNC({{ p }}{{ column_name }}) {{ alias|as_kw }}