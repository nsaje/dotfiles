CASE
    WHEN SUM({{ p }}impressions) <> 0
        THEN (SUM(CASE WHEN {{ p }}impressions IS NOT NULL THEN {{ p }}cost_nano ELSE 0 END)::float / (SUM({{ p }}impressions) / 1000.0)) / 1000000000.0
    ELSE NULL
END {{ alias }}
