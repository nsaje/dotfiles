-- AVG when 0 or between [0.8, 1.0)
-- metric_value: TRUNC(CASE WHEN {{ has_conversion_key }} THEN {{ cost_column }} / NULLIF({{ conversion_key }}, 0) ELSE {{ metric_column }} END, {{ metric_val_decimal_places }})
CASE
  WHEN
      {{ is_cost_dependent }}
      AND TRUNC(NVL({{ cost_column }}, 0), 2) > 0  -- has cost
      AND NVL(
            TRUNC(CASE WHEN {{ has_conversion_key }} THEN {{ cost_column }} / NULLIF({{ conversion_key }}, 0) ELSE {{ metric_column }} END, {{ metric_val_decimal_places }})  -- metric value
          , 0) = 0 -- no spend
    THEN 0 -- underperforming
  WHEN
      (CASE WHEN {{ has_conversion_key }} THEN {{ cost_column }} / NULLIF({{ conversion_key }}, 0) ELSE {{ metric_column }} END) -- metric value
      IS NULL OR {{ planned_value }} IS NULL
    THEN NULL  -- not determined
  WHEN {{ is_inverse_performance }}
    THEN (2 * {{ planned_value }} -
           TRUNC((CASE WHEN {{ has_conversion_key }} THEN {{ cost_column }} / NULLIF({{ conversion_key }}, 0) ELSE {{ metric_column }} END), {{ metric_val_decimal_places }}) -- metric value
         ) / NULLIF({{ planned_value }}, 0)::float
  ELSE
       TRUNC(CASE WHEN {{ has_conversion_key }} THEN {{ cost_column }} / NULLIF({{ conversion_key }}, 0) ELSE {{ metric_column }} END, {{ metric_val_decimal_places }}) -- metric value
       / NULLIF({{ planned_value }}, 0)::float
END {{ alias }}
