CREATE TABLE IF NOT EXISTS mv_master_pubs (
        -- kw::dimensions
        date date not null,
        source_id int2,

        account_id integer,
        campaign_id integer,
        ad_group_id integer,

        publisher varchar(255),
        publisher_source_id varchar(260),
        external_id varchar(255),

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
        video_progress_3s integer,

        local_cost_nano bigint,
        local_data_cost_nano bigint,
        local_effective_cost_nano bigint,
        local_effective_data_cost_nano bigint,
        local_license_fee_nano bigint,
        local_margin_nano bigint
        -- kw::end
);
CREATE INDEX IF NOT EXISTS mv_master_pubs_main_idx ON mv_master_pubs (source_id, account_id, campaign_id, ad_group_id, publisher_source_id, date);
CREATE STATISTICS IF NOT EXISTS mv_master_pubs_stx (dependencies) ON account_id, campaign_id, ad_group_id FROM mv_master_pubs;
