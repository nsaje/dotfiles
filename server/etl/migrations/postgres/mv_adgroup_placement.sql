CREATE TABLE IF NOT EXISTS mv_adgroup_placement (
    -- kw::dimensions
    date date not null,

    account_id integer,
    campaign_id integer,
    ad_group_id integer,

    source_id int2,
    publisher varchar(255),
    publisher_source_id varchar(260),
    placement_type integer,
    placement varchar(127),

    -- kw::aggregates
    impressions integer,
    clicks integer,

    cost_nano bigint,
    data_cost_nano bigint,
    effective_cost_nano bigint,
    effective_data_cost_nano bigint,
    license_fee_nano bigint,
    margin_nano bigint,

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
    local_margin_nano bigint,

    visits integer,
    new_visits integer,
    bounced_visits integer,
    pageviews integer,
    total_time_on_site integer,
    users integer,
    returning_users integer,

    mrc50_measurable integer,
    mrc50_viewable integer,
    mrc100_measurable integer,
    mrc100_viewable integer,
    vast4_measurable integer,
    vast4_viewable integer,

    ssp_cost_nano bigint,
    local_ssp_cost_nano bigint,

    base_effective_cost_nano bigint,
    base_effective_data_cost_nano bigint,
    service_fee_nano bigint,

    local_base_effective_cost_nano bigint,
    local_base_effective_data_cost_nano bigint,
    local_service_fee_nano bigint,

    -- kw::dimensions
    outbrain_publisher_id varchar(127),
    outbrain_section_id varchar(127),
    original_source_id int2
    -- kw::end
);
CREATE INDEX IF NOT EXISTS mv_adgroup_placement_main_idx ON mv_adgroup_placement (source_id, account_id, campaign_id, ad_group_id, publisher_source_id, placement_type, placement, date);
CREATE STATISTICS IF NOT EXISTS mv_adgroup_placement_stx (dependencies) ON account_id, campaign_id, ad_group_id FROM mv_adgroup_placement;
