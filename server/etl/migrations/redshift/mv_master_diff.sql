CREATE TABLE mv_master_diff (
       date date not null encode delta,
       source_id int2 encode bytedict,

       account_id integer encode zstd,
       campaign_id integer encode zstd,
       ad_group_id integer encode zstd,
       content_ad_id integer encode zstd,
       publisher varchar(255) encode zstd,

       device_type int2 encode zstd,

       country varchar(2) encode zstd,
       state varchar(32) encode zstd,
       dma int2 encode bytedict,

       age varchar(10) encode zstd,
       gender varchar(10) encode zstd,
       age_gender varchar(21) encode zstd,

       impressions integer encode zstd,
       clicks integer encode zstd,
       cost_nano bigint encode zstd,
       data_cost_nano bigint encode zstd,

       visits integer encode zstd,
       new_visits integer encode zstd,
       bounced_visits integer encode zstd,
       pageviews integer encode zstd,
       total_time_on_site integer encode zstd,

       effective_cost_nano bigint encode zstd,
       effective_data_cost_nano bigint encode zstd,
       license_fee_nano bigint encode zstd,

       users integer encode lzo,
       returning_users integer encode lzo

       local_cost_nano bigint encode zstd,
       local_data_cost_nano bigint encode zstd,
       local_effective_cost_nano bigint encode zstd,
       local_effective_data_cost_nano bigint encode zstd,
       local_license_fee_nano bigint encode zstd,
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, content_ad_id);
