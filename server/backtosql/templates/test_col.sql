{% load backtosql_tags %}
SUM({{ p }}{{ column_name }})*{{ multiplier }}{{ alias|_as_ }}
