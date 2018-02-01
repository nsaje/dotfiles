{% load backtosql_tags %}

{% for table in temp_tables %}
DROP TABLE {{ table.name }};
{% endfor %}
