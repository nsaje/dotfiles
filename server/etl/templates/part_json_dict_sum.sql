{% load backtosql_tags %}
json_dict_sum(LISTAGG({{ p }}{{ column_name }}, ';'), ';')  {{ alias|as_kw }}