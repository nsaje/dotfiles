{% load backtosql_tags %}

{% for name, values in tmp_tables %}
create temp table {{ name }} (id {{ values|values_type }});
insert into {{ name }} (id) values {{ values|values_for_insert }};
{% endfor %}
