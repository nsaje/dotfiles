CASE WHEN (NVL(SUM({{ p }}visits)) - NVL(SUM({{ p }}bounced_visits), 0)) <> 0
     -- convert from nano
     THEN (CAST(SUM(effective_cost_nano) AS FLOAT) / (1000000000.0 * (NVL(SUM(visits), 0) - NVL(SUM(bounced_visits), 0))))
     ELSE NULL
END {{ alias }}