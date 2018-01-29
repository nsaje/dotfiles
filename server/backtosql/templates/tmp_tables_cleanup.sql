{% for name, _ in tmp_tables %}
drop table {{ name }};
{% endfor %}
