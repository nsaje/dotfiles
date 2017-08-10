SUM({{ p }}{{ column_name }})::FLOAT / (
NULLIF(SUM({{ p }}{{ divisor }}), 0) * {% firstof divisor_modifier 1 %})
{{ alias }}
