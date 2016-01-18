create table publishers_1(
  date date not null,
  adgroup_id integer not null,
  exchange varchar(255),
  name varchar(255),
  external_id varchar(255),
  clicks int,
  impressions int,
  cost_micro bigint,
  data_cost_micro bigint,
  effective_cost_nano bigint,
  effective_data_cost_nano bigint,
  license_fee_nano bigint,
  unique (date, adgroup_id, exchange, domain))
sortkey(date, adgroup_id);
