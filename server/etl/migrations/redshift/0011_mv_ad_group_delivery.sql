CREATE TABLE mv_ad_group_delivery (
       date date not null encode delta,
       source_id int2 encode bytedict,

       agency_id int2 encode lzo,
       account_id int2 encode lzo,
       campaign_id int2 encode lzo,
       ad_group_id int2 encode lzo,

       device_type integer encode bytedict,
       country varchar(2) encode bytedict,
       state varchar(5) encode bytedict,
       dma int2 encode bytedict,
       age int2 encode bytedict,
       gender int2 encode bytedict,
       age_gender int2 encode bytedict,

       impressions integer encode lzo,
       clicks integer encode lzo,
       cost_nano bigint encode lzo,
       data_cost_nano bigint encode lzo,

       visits integer encode lzo,
       new_visits integer encode lzo,
       bounced_visits integer encode lzo,
       pageviews integer encode lzo,
       total_time_on_site integer encode lzo,

       effective_cost_nano bigint encode lzo,
       effective_data_cost_nano bigint encode lzo,
       license_fee_nano bigint encode lzo,
       margin_nano bigint encode lzo,

       users integer encode lzo,
       returning_users integer encode lzo
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, device_type, country, state, age);
