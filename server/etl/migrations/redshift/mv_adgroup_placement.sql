CREATE TABLE mv_adgroup_placement (
    -- kw::dimensions
    date date not null encode AZ64,

    account_id integer encode AZ64,
    campaign_id integer encode AZ64,
    ad_group_id integer encode AZ64,

    source_id int2 encode AZ64,
    publisher varchar(255) encode zstd,
    publisher_source_id varchar(260) encode zstd,
    placement_type integer encode AZ64,
    placement varchar(127) encode zstd,

    -- kw::aggregates
    impressions integer encode AZ64,
    clicks integer encode AZ64,
    cost_nano bigint encode AZ64,
    data_cost_nano bigint encode AZ64,

    effective_cost_nano bigint encode AZ64,
    effective_data_cost_nano bigint encode AZ64,
    license_fee_nano bigint encode AZ64,
    margin_nano bigint encode AZ64,

    video_start integer encode AZ64,
    video_first_quartile integer encode AZ64,
    video_midpoint integer encode AZ64,
    video_third_quartile integer encode AZ64,
    video_complete integer encode AZ64,
    video_progress_3s integer encode AZ64,

    local_cost_nano bigint encode AZ64,
    local_data_cost_nano bigint encode AZ64,
    local_effective_cost_nano bigint encode AZ64,
    local_effective_data_cost_nano bigint encode AZ64,
    local_license_fee_nano bigint encode AZ64,
    local_margin_nano bigint encode AZ64
-- kw::end
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, publisher_source_id, placement_type, placement);
