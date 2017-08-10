(NVL(SUM({{ p }}{{ column_name1 }}), 0) +
 NVL(SUM({{ p }}{{ column_name2 }}), 0) +
 NVL(SUM({{ p }}{{ column_name3 }}), 0) +
 NVL(SUM({{ p }}{{ column_name4 }}), 0)
)::float/1000000000 {{ alias }}
