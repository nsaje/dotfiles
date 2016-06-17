-- table definition for the master materialized view table
-- it can be quite big - use even distribution (default)
CREATE TABLE mv_master (
       date date not null encode delta,
       source_id int2 encode bytedict,

       agency_id int2 encode lzo,
       account_id int2 encode lzo,
       campaign_id int2 encode lzo,
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
       cost_cc integer encode lzo,
       data_cost_cc integer encode lzo,

       visits integer encode lzo,
       new_visits integer encode lzo,
       bounced_visits integer encode lzo,
       pageviews integer encode lzo,
       total_time_on_site integer encode lzo,

       effective_cost_nano bigint encode lzo,
       effective_data_cost_nano bigint encode lzo,
       license_fee_nano bigint encode lzo
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, content_ad_id);
