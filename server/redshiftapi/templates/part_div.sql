(COALESCE({{ p }}{{ column_name }}, 0))::FLOAT /
(NULLIF({{ p }}{{ divisor }}, 0) * {% firstof divisor_modifier 1 %})
{{ alias }}
