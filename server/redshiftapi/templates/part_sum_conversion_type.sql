SUM(
  CASE
    WHEN {{ conversion_type }}=1 AND (type=1 OR type IS NULL) OR {{ conversion_type }}=2 AND type=2
    THEN {{ p }}{{ column_name }}
    ELSE 0
  END
) {{ alias }}
