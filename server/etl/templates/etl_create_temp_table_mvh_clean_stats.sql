CREATE TEMP TABLE mvh_clean_stats (
    date date not null encode delta,
    source_slug varchar(127) encode lzo,

    ad_group_id integer encode lzo,
    content_ad_id integer encode lzo,
    publisher varchar(255) encode lzo,

    device_type int2 encode bytedict,
    country varchar(2) encode bytedict,
    state varchar(5) encode bytedict,
    dma int2 encode bytedict,
    city_id integer encode lzo,

    placement_type integer encode lzo,
    video_playback_method integer encode lzo,

    age int2 encode bytedict,
    gender int2 encode bytedict,
    age_gender int2 encode bytedict,

    impressions integer encode lzo,
    clicks integer encode lzo,
    spend bigint encode lzo,
    data_spend bigint encode lzo,

    video_start integer encode lzo,
    video_first_quartile integer encode lzo,
    video_midpoint integer encode lzo,
    video_third_quartile integer encode lzo,
    video_complete integer encode lzo,
    video_progress_3s integer encode lzo
) distkey(date) sortkey(date, source_slug, ad_group_id, content_ad_id, publisher)
