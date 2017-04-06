{% load backtosql_tags %}
CASE
  WHEN {{ p }}{{ source_column }} = '{{ yahoo_value }}' THEN NULL ELSE {{ p }}{{ column_name }}
END {{ alias|as_kw }}
