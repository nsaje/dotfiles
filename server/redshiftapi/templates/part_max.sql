{% load backtosql_tags %}
MAX({{ p }}{{ column_name }}){{ alias|as_kw }}
