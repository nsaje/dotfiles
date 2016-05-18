{% load backtosql_tags %}
SUM({{ p }}{{ column_name }})*{{ multiplier }}{{ alias|as_kw }}
