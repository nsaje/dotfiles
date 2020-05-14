CREATE TABLE mv_master_pubs (
        -- kw::dimensions
        date date not null encode delta,
        source_id int2 encode zstd,

        account_id integer encode zstd,
        campaign_id integer encode zstd,
        ad_group_id integer encode zstd,

        publisher varchar(255) encode zstd,
        publisher_source_id varchar(260) encode zstd,
        external_id varchar(255) encode zstd,

        device_type int2 encode zstd,
        device_os varchar(127) encode lzo,
        device_os_version varchar(127) encode lzo,
        environment varchar(10) encode zstd,

        zem_placement_type int2 encode lzo,
        video_playback_method int2 encode lzo,

        country varchar(2) encode zstd,
        state varchar(32) encode bytedict,
        dma int2 encode bytedict,
        city_id integer encode zstd,

        age varchar(10) encode zstd,
        gender varchar(10) encode zstd,
        age_gender varchar(21) encode zstd,

        -- kw::aggregates
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
        margin_nano bigint encode zstd,

        users integer encode lzo,
        returning_users integer encode lzo,

        video_start integer encode lzo,
        video_first_quartile integer encode lzo,
        video_midpoint integer encode lzo,
        video_third_quartile integer encode lzo,
        video_complete integer encode lzo,
        video_progress_3s integer encode lzo,

        local_cost_nano bigint encode zstd,
        local_data_cost_nano bigint encode zstd,
        local_effective_cost_nano bigint encode zstd,
        local_effective_data_cost_nano bigint encode zstd,
        local_license_fee_nano bigint encode zstd,
        local_margin_nano bigint encode zstd,

        mrc50_measurable integer encode AZ64,
        mrc50_viewable integer encode AZ64,
        mrc100_measurable integer encode AZ64,
        mrc100_viewable integer encode AZ64,
        vast4_measurable integer encode AZ64,
        vast4_viewable integer encode AZ64,

        ssp_cost_nano bigint encode AZ64,
        local_ssp_cost_nano bigint encode AZ64
        -- kw::end
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, publisher_source_id);
