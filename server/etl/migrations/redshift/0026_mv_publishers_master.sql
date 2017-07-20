CREATE TABLE mv_pubs_master (
       date date not null encode delta,
       source_id int2 encode bytedict,

       agency_id int2 encode lzo,
       account_id int2 encode lzo,
       campaign_id integer encode lzo,
       ad_group_id integer encode lzo,
       publisher varchar(255) encode lzo,
       external_id varchar(255) encode lzo,

       device_type int2 encode bytedict,
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
       returning_users integer encode lzo,

       city_id integer encode lzo,

       -- video
       placement_type int2 encode lzo,
       video_playback_method int2 encode lzo,
       video_start integer encode lzo,
       video_first_quartile integer encode lzo,
       video_midpoint integer encode lzo,
       video_third_quartile integer encode lzo,
       video_complete integer encode lzo,
       video_progress_3s integer encode lzo
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, publisher);
