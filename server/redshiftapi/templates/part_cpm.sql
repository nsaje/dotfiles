CASE
    WHEN SUM({{ p }}impressions) <> 0
        THEN (SUM({{ p }}cost_nano)::float / (SUM({{ p }}impressions) / 1000.0)) / 1000000000.0
    ELSE NULL
END {{ alias }}
