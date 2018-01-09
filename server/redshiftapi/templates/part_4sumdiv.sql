(
  COALESCE(SUM({{ p }}{{ column_name1 }})::FLOAT, 0) +
  COALESCE(SUM({{ p }}{{ column_name2 }})::FLOAT, 0) +
  COALESCE(SUM({{ p }}{{ column_name3 }})::FLOAT, 0) +
  COALESCE(SUM({{ p }}{{ column_name4 }})::FLOAT, 0)
)::FLOAT / (NULLIF(SUM({{ p }}{{ divisor }}), 0) * {% firstof divisor_modifier 1 %})
{{ alias }}
