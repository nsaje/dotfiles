{% autoescape off%}

({{ first_table_column }} = {{ second_table_column }} OR {{ first_table_column }} IS NULL AND {{ second_table_column }} IS NULL)
{% endautoescape %}
