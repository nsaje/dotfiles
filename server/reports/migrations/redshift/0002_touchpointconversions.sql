CREATE TABLE touchpointconversions (
    zuid varchar(64) encode lzo,
    slug varchar(256) encode lzo,

    date date encode lzo,

    conversion_id varchar(64) encode lzo,
    conversion_timestamp timestamp encode lzo,

    account_id integer encode lzo,
    campaign_id integer encode lzo,
    ad_group_id integer  encode lzo,
    content_ad_id integer encode lzo,
    source_id integer encode bytedict,

    touchpoint_id varchar(64) encode lzo,
    touchpoint_timestamp timestamp encode lzo,
    conversion_lag integer encode lzo,

    publisher varchar(255) default null encode lzo
)
DISTSTYLE EVEN
SORTKEY (date, account_id, slug, source_id, campaign_id, ad_group_id, content_ad_id, publisher, touchpoint_id);