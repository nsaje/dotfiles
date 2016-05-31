{% load backtosql_tags %}
-- aggregates number of touchpoint conversions by conversion windows.
-- NOTE: does not include same window in longer windows. This information should be retrieved
-- in the postprocess phase.
CASE
  WHEN {{ p }}{{ column_name }} <= {{ conversion_windows.0 }} THEN {{ conversion_windows.0 }}
  WHEN {{ p }}{{ column_name }} > {{ conversion_windows.0 }} AND {{ p }}{{ column_name }} <= {{ conversion_windows.1 }} THEN {{ conversion_windows.1 }}
  ELSE {{ conversion_windows.2 }}
END {{ alias|as_kw }}