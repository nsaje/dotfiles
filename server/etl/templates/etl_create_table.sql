{% autoescape on %}
CREATE TABLE IF NOT EXISTS {{ table_name }} (
    {{ column_definitions|join:", " }}
)
diststyle {{ diststyle }}
{% if distkey %}distkey({{ distkey }}){% endif %}
sortkey({{ sortkey|join:"," }})
{% endautoescape %}
