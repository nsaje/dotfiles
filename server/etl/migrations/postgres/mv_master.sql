-- table definition for the master materialized view table
CREATE TABLE mv_master (
       -- kw::dimensions
       date date not null,
       source_id int2,

       account_id integer,
       campaign_id integer,
       ad_group_id integer,
       content_ad_id integer,

       publisher varchar(255),
       publisher_source_id varchar(260),

       device_type int2,
       device_os varchar(127),
       device_os_version varchar(127),
       placement_medium varchar(10),

       placement_type int2,
       video_playback_method int2,

       country varchar(2),
       state varchar(32),
       dma int2,
       city_id integer,

       age varchar(10),
       gender varchar(10),
       age_gender varchar(21),

       -- kw::aggregates
       impressions integer,
       clicks integer,
       cost_nano bigint,
       data_cost_nano bigint,

       visits integer,
       new_visits integer,
       bounced_visits integer,
       pageviews integer,
       total_time_on_site integer,

       effective_cost_nano bigint,
       effective_data_cost_nano bigint,
       license_fee_nano bigint,
       margin_nano bigint,

       users integer,
       returning_users integer,

       video_start integer,
       video_first_quartile integer,
       video_midpoint integer,
       video_third_quartile integer,
       video_complete integer,
       video_progress_3s integer
       -- kw::end
);
CREATE INDEX IF NOT EXISTS mv_master_main_idx ON mv_master (source_id, account_id, campaign_id, ad_group_id, content_ad_id, publisher_source_id, date);
