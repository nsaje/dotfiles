{% autoescape on %}
CREATE TABLE IF NOT EXISTS {{ table_name }} (
    {{ dimensions|join:", " }},
    {{ aggregates|join:", " }}
);
CREATE INDEX IF NOT EXISTS {{ table_name }}_main_idx ON {{ table_name }} ({{ index|join:"," }});
{% endautoescape %}
