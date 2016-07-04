{% load backtosql_tags %}
{% autoescape off%}

{{ p }}{{ column_name }}{{ alias|as_kw }}
{% endautoescape %}
