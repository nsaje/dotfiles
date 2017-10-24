CREATE TABLE mv_conversions (
      -- kw::dimensions
      date date not null encode delta,
      source_id int2 encode zstd,

      account_id integer encode zstd,
      campaign_id integer encode zstd,
      ad_group_id integer encode zstd,
      content_ad_id integer encode zstd,

      publisher varchar(255) encode zstd,
      publisher_source_id varchar(260) encode zstd,

      slug varchar(256) encode zstd,

      -- kw::aggregates
      conversion_count integer encode zstd
      -- kw::end
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, content_ad_id, publisher_source_id, slug);
