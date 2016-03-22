(CASE
  WHEN SUM({{ p }}clicks) = 0 THEN NULL
  WHEN SUM({{ p }}visits) = 0 THEN 1
  WHEN SUM({{ p }}clicks) < SUM({{ p }}visits) THEN 0
  ELSE (SUM(CAST({{ p }}clicks AS FLOAT)) - SUM({{ p }}visits)) / SUM({{ p }}clicks)
END)*100.0 {{ alias }}