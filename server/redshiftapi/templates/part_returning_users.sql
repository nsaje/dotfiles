CASE
  WHEN SUM({{ p }}users) IS NULL OR SUM({{ p }}new_visits) IS NULL THEN NULL
  WHEN SUM({{ p }}new_visits) > SUM({{ p }}users) THEN 0
  ELSE SUM({{ p }}users) - SUM({{ p }}new_visits)
END {{ alias }}
