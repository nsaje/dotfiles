{% autoescape on %}
CREATE TABLE IF NOT EXISTS {{ table_name }} (
    {{ dimensions|join:", " }},
    {{ aggregates|join:", " }}
);
CREATE INDEX IF NOT EXISTS {{ table_name }}_main_idx ON {{ table_name }} ({{ index|join:"," }});
{% if dependencies and dependencies|length > 1 %}
CREATE STATISTICS IF NOT EXISTS {{ table_name }}_stx (dependencies) ON {{ dependencies|join:"," }} FROM {{ table_name }};
{% endif %}
{% endautoescape %}
