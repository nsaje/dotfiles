CREATE TEMP TABLE mvh_clean_stats (
    date date not null encode delta,
    source_slug varchar(127) encode zstd,

    ad_group_id integer encode zstd,
    content_ad_id integer encode zstd,
    publisher varchar(255) encode zstd,

    device_type integer encode bytedict,
    device_os varchar(127) encode bytedict,
    device_os_version varchar(127) encode zstd,
    environment varchar(10) encode bytedict,

    zem_placement_type int2 encode zstd,
    video_playback_method int2 encode zstd,

    country varchar(2) encode zstd,
    state varchar(32) encode zstd,
    dma int2 encode bytedict,
    city_id integer encode lzo,

    age varchar(10) encode zstd,
    gender varchar(10) encode zstd,
    age_gender varchar(21) encode zstd,

    impressions integer encode zstd,
    clicks integer encode zstd,
    spend bigint encode zstd,
    data_spend bigint encode zstd,

    video_start integer encode lzo,
    video_first_quartile integer encode lzo,
    video_midpoint integer encode lzo,
    video_third_quartile integer encode lzo,
    video_complete integer encode lzo,
    video_progress_3s integer encode lzo,

    mrc50_measurable integer encode AZ64,
    mrc50_viewable integer encode AZ64,
    mrc100_measurable integer encode AZ64,
    mrc100_viewable integer encode AZ64,
    vast4_measurable integer encode AZ64,
    vast4_viewable integer encode AZ64,

    ssp_spend bigint encode AZ64
) distkey(date) sortkey(date, source_slug, ad_group_id, content_ad_id, publisher)
