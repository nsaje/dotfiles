create table publishers_3 (
  date date not null encode delta,
  adgroup_id integer not null encode lzo,
  exchange varchar(255) encode lzo,
  domain varchar(255) encode lzo,
  external_id varchar(255) encode lzo,
  clicks int encode lzo,
  impressions int encode bytedict,
  cost_nano bigint encode lzo,
  data_cost_nano bigint encode lzo,
  effective_cost_nano bigint encode lzo,
  effective_data_cost_nano bigint encode lzo,
  license_fee_nano bigint encode lzo,
  visits integer encode lzo,
  new_visits integer encode lzo,
  bounced_visits integer encode lzo,
  pageviews integer encode lzo,
  total_time_on_site integer encode lzo,
  conversions varchar(2048) encode lzo,
  unique (date, adgroup_id, exchange, domain))
distkey(date)
sortkey(date, adgroup_id);