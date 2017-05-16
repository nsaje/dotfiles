CREATE TABLE mv_touch_account (
    date date not null encode delta,
    source_id int2 encode bytedict,

    agency_id int2 encode lzo,
    account_id int2 encode lzo,

    slug varchar(256) encode lzo,
    conversion_window integer encode lzo,

    touchpoint_count integer encode lzo,
    conversion_count integer encode lzo,

    conversion_value_nano bigint encode lzo
) sortkey(date, source_id, account_id, slug, conversion_window, agency_id);
