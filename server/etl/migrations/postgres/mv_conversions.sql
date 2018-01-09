CREATE TABLE mv_conversions (
      -- kw::dimensions
      date date not null,
      source_id int2,

      account_id integer,
      campaign_id integer,
      ad_group_id integer,
      content_ad_id integer,

      publisher varchar(255),
      publisher_source_id varchar(260),

      slug varchar(256),

      -- kw::aggregates
      conversion_count integer
      -- kw::end
);
CREATE INDEX IF NOT EXISTS mv_conversions_main_idx ON mv_conversions (source_id, account_id, campaign_id, ad_group_id, content_ad_id, publisher_source_id, slug, date);
