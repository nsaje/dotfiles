{% autoescape on %}
CREATE TABLE IF NOT EXISTS {{ table_name }} (
    {{ dimensions|join:", " }},
    {{ aggregates|join:", " }}
)
diststyle {{ diststyle }}
{% if distkey %}distkey({{ distkey }}){% endif %}
sortkey({{ sortkey|join:"," }})
{% endautoescape %}
