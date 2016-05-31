{% load backtosql_tags %}
-- aggregates number of touchpoint conversions by conversion windows.
-- NOTE: does not include same window in longer windows. This information should be retrieved
-- in the postprocess phase.
CASE
  WHEN {{ p }}{{ column_name }} <= {{ conversion_lags|first }} THEN {{ conversion_lags|first }}
  {% for r in conversion_lags|slice:"1:-1" %}
  WHEN {{ p }}{{ column_name }} > {{ r }} AND {{ p }}{{ column_name }} <= {{ r }} THEN {{ r }}
  {% endfor %}
  ELSE {{ conversion_lags|last }}
END {{ alias|as_kw }}