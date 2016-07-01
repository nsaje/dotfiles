{% load backtosql_tags %}
{% autoescape off%}

{{ column_render }}{{ direction|lspace }}
{% endautoescape %}
