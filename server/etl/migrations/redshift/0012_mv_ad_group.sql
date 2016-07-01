CREATE TABLE mv_ad_group (
       date date not null encode delta,
       source_id int2 encode bytedict,

       agency_id int2 encode lzo,
       account_id int2 encode lzo,
       campaign_id int2 encode lzo,
       ad_group_id int2 encode lzo,

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

) distkey(date) sortkey(date, source_id, account_id, campaign_id, ad_group_id);
