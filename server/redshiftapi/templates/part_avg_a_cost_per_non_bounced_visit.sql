SUM({{ p }}cost_nano)::float
/ NULLIF(
  (  NVL( SUM( {{ p }}visits ), 0 ) -
     NVL( SUM( {{ p }}bounced_visits ), 0 )
  ) * 1000000000, 0 )
{{ alias }}
