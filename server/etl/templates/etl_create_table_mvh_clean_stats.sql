create table mvh_clean_stats (
  date date not null encode delta,
  source_slug varchar(127) encode lzo,

  ad_group_id int2 encode lzo,
  content_ad_id integer encode lzo,
  publisher varchar(255) encode lzo,

  device_type int2 encode bytedict,
  country varchar(2) encode bytedict,
  state varchar(5) encode bytedict,
  dma int2 encode bytedict,
  age int2 encode bytedict,
  gender int2 encode bytedict,
  age_gender int2 encode bytedict,

  impressions integer encode lzo,
  clicks integer encode lzo,
  spend bigint encode lzo,
  data_spend bigint encode lzo
) distkey(date) sortkey(date, source_slug, ad_group_id, content_ad_id, publisher)