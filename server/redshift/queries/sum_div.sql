CASE WHEN SUM({{ p+divisor }}) <> 0 THEN SUM(CAST({{ p+expr }}) AS FLOAT) / SUM({{ p+divisor }}) ELSE NULL END {{ alias }}
