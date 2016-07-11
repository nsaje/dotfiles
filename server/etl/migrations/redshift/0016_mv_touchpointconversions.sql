CREATE TABLE mv_touchpointconversions (
    date date not null encode delta,
    source_id int2 encode bytedict,

    agency_id int2 encode lzo,
    account_id int2 encode lzo,
    campaign_id int2 encode lzo,
    ad_group_id int2 encode lzo,
    content_ad_id integer encode lzo,
    publisher varchar(255) encode lzo,

    slug varchar(256) encode lzo,
    conversion_window integer encode lzo,

    touchpoint_count integer encode lzo
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, content_ad_id, conversion_window);