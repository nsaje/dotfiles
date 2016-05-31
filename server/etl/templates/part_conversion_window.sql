{% load backtosql_tags %}
-- Adds conversion window dimension that joins conversion window ranges into predefined drawers.
-- NOTE: does not include same window in longer windows. This information should be retrieved
-- in the postprocess phase: conversion lag 5 would be counted under 7 but not under 10 (imaginary numbers).
CASE
  WHEN {{ p }}{{ column_name }} <= {{ conversion_windows.0 }} THEN {{ conversion_windows.0 }}
  WHEN {{ p }}{{ column_name }} > {{ conversion_windows.0 }} AND {{ p }}{{ column_name }} <= {{ conversion_windows.1 }}
      THEN {{ conversion_windows.1 }}
  ELSE {{ conversion_windows.2 }}
END {{ alias|as_kw }}