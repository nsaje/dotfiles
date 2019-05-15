SUM(
  CASE
    WHEN {{ p }}slug='{{ slug }}'
    AND {{ p }}account_id={{ account_id }}
    AND {{ p }}conversion_window<={{ window }}
    AND (
        {{ type }}=1 AND ({{ p }}type=1 OR {{ p }}type IS NULL)
        OR {{ type }}=2 AND {{ p }}type=2
    )
    THEN conversion_count
    ELSE 0
  END
) {{ alias }}
