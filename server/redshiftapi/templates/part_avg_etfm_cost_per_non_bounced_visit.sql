( COALESCE( SUM({{ p }}effective_cost_nano), 0 ) +
  COALESCE( SUM({{ p }}effective_data_cost_nano), 0 ) +
  COALESCE( SUM({{ p }}license_fee_nano), 0 ) +
  COALESCE( SUM({{ p }}margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( {{ p }}visits ), 0 ) -
     COALESCE( SUM( {{ p }}bounced_visits ), 0 )
  ) * 1000000000, 0 )
{{ alias }}
