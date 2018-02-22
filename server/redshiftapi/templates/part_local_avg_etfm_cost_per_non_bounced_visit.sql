( COALESCE( SUM({{ p }}local_effective_cost_nano), 0 ) +
  COALESCE( SUM({{ p }}local_effective_data_cost_nano), 0 ) +
  COALESCE( SUM({{ p }}local_license_fee_nano), 0 ) +
  COALESCE( SUM({{ p }}local_margin_nano), 0 )
)::float
/ NULLIF(
  (  COALESCE( SUM( {{ p }}visits ), 0 ) -
     COALESCE( SUM( {{ p }}bounced_visits ), 0 )
  ) * 1000000000, 0 )
{{ alias }}
