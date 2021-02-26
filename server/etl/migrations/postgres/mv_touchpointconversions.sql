CREATE TABLE IF NOT EXISTS mv_touchpointconversions (
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
      environment varchar(10),

      country varchar(2),
      state varchar(32),
      dma int2,

      slug varchar(256),
      conversion_window integer,
      conversion_label varchar(256),

      -- kw::aggregates
      touchpoint_count integer,
      conversion_count integer,
      conversion_value_nano bigint,

      -- kw::dimensions
      type int2,
      placement varchar(127),
      placement_type int,
      browser varchar(127),
      connection_type varchar(127),
      original_source_id int2
      -- kw::end
);
CREATE INDEX IF NOT EXISTS mv_touchpointconversions_main_idx ON mv_touchpointconversions (source_id, account_id, campaign_id, ad_group_id, content_ad_id, slug, conversion_window, date);
CREATE STATISTICS IF NOT EXISTS mv_touchpointconversions_stx (dependencies) ON account_id, campaign_id, ad_group_id, content_ad_id FROM mv_touchpointconversions;
CREATE STATISTICS IF NOT EXISTS mv_touchpointconversions_stx_slug (dependencies) ON account_id, slug FROM mv_touchpointconversions;
