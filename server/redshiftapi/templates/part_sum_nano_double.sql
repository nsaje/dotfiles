(NVL(SUM({{ p }}{{ column_name1 }}), 0) + NVL(SUM({{ p }}{{ column_name2 }}), 0))/1000000000.0 {{ alias }}
