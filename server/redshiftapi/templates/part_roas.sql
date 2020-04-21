(CASE WHEN COALESCE({{cost_column}}, 0) = 0 THEN NULL ELSE COALESCE(total_conversion_value_{{conversion_key}}, 0) / COALESCE({{ cost_column }}, 1) END) {{ alias }}
