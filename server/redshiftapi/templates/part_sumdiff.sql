(
    COALESCE(SUM({{ p }}{{ column_name1 }}), 0) -
    COALESCE(SUM({{ p }}{{ column_name2 }}), 0)
) {{ alias }}
