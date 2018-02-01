{% load backtosql_tags %}

{% for table in temp_tables %}
CREATE TEMP TABLE {{ table.name }} ({{ table.constraint }} {{ table.values_type }});
INSERT INTO {{ table.name }} ({{ table.constraint }}) VALUES {{ table.values_insert_template }};
{% endfor %}
