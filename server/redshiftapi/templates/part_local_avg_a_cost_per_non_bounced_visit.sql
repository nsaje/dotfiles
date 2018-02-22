SUM({{ p }}local_cost_nano)::float
/ NULLIF(
  (  COALESCE( SUM( {{ p }}visits ), 0 ) -
     COALESCE( SUM( {{ p }}bounced_visits ), 0 )
  ) * 1000000000, 0 )
{{ alias }}
