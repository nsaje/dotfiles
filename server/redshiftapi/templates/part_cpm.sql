(SUM(cost_nano)::float / (NULLIF(SUM({{ p }}impressions), 0) / 1000.0)) / 1000000000.0 {{ alias }}
