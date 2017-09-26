CREATE TABLE mv_content_ad (
       date date not null encode delta,
       source_id int2 encode bytedict,

       agency_id int2 encode lzo,
       account_id int2 encode lzo,
       campaign_id integer encode lzo,
       ad_group_id integer encode lzo,
       content_ad_id integer encode lzo,

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

       video_start integer encode lzo,
       video_first_quartile integer encode lzo,
       video_midpoint integer encode lzo,
       video_third_quartile integer encode lzo,
       video_complete integer encode lzo,
       video_progress_3s integer encode lzo
) distkey(date) sortkey(date, source_id, account_id, campaign_id, ad_group_id, content_ad_id);
