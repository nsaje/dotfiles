CREATE TABLE mv_pubs_ad_group (
       date date not null encode delta,
       source_id int2 encode bytedict,

       agency_id int2 encode lzo,
       account_id int2 encode lzo,
       campaign_id int2 encode lzo,
       ad_group_id int2 encode lzo,
       publisher varchar(255) encode lzo,
       external_id varchar(255) encode lzo,

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
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, publisher);