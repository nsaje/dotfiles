CREATE TABLE mv_conversions_content_ad (
    date date not null encode delta,
    source_id int2 encode bytedict,

    agency_id int2 encode lzo,
    account_id int2 encode lzo,
    campaign_id integer encode lzo,
    ad_group_id integer encode lzo,
    content_ad_id integer encode lzo,

    slug varchar(256) encode lzo,

    conversion_count integer encode lzo
) sortkey(date, source_id, account_id, campaign_id, ad_group_id, content_ad_id, slug, agency_id);