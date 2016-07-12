CREATE TABLE mv_touch_campaign (
    date date not null encode delta,
    source_id int2 encode bytedict,

    agency_id int2 encode lzo,
    account_id int2 encode lzo,
    campaign_id int2 encode lzo,

    slug varchar(256) encode lzo,
    conversion_window integer encode lzo,

    touchpoint_count integer encode lzo,
    conversion_count integer encode lzo
) sortkey(date, source_id, account_id, campaign_id, slug, conversion_window, agency_id);