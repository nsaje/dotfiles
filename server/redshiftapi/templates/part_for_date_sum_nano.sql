SUM(
    CASE WHEN {{ p }}{{ date_column_name }}='{{ date }}' THEN {{ p }}{{ column_name }}
    ELSE 0 END
    )/1000000000.0 {{ alias }}