SUM(effective_cost_nano)::float / (NULLIF(SUM({{ p }}total_time_on_site), 0) * 1000000000.0) {{ alias }}