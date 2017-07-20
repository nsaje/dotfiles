CREATE TABLE mv_conversions_campaign (
    date date not null encode delta,
    source_id int2 encode bytedict,

    agency_id int2 encode lzo,
    account_id int2 encode lzo,
    campaign_id integer encode lzo,

    slug varchar(256) encode lzo,

    conversion_count integer encode lzo
) sortkey(date, source_id, account_id, campaign_id, slug, agency_id);