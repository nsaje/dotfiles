{% load backtosql_tags %}
json_dict_sum(LISTAGG({{ p }}{{ column_name }}, '\n'), '\n')  {{ alias|as_kw }}