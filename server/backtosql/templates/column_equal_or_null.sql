{% autoescape off%}

{% if null == True %}
({{ first_table_column }} = {{ second_table_column }} OR {{ first_table_column }} IS NULL AND {{ second_table_column }} IS NULL)
{% else %}
{{ first_table_column }} = {{ second_table_column }}
{% endif %}

{% endautoescape %}
