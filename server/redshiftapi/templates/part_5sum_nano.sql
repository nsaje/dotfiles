(COALESCE(SUM({{ p }}{{ column_name1 }}), 0) +
 COALESCE(SUM({{ p }}{{ column_name2 }}), 0) +
 COALESCE(SUM({{ p }}{{ column_name3 }}), 0) +
 COALESCE(SUM({{ p }}{{ column_name4 }}), 0) +
 COALESCE(SUM({{ p }}{{ column_name5 }}), 0)
)::float/1000000000 {{ alias }}
