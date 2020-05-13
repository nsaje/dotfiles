( 
    COALESCE(SUM({{ p }}{{ column_name1 }}), 0) -
    COALESCE(SUM({{ p }}{{ column_name2 }}), 0)
)::FLOAT / (
    NULLIF(SUM({{ p }}{{ divisor }}), 0) * {% firstof divisor_modifier 1 %}
)
{{ alias }}
