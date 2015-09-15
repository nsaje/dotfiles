CREATE TABLE touchpointconversions (
    zuid varchar(64),
    slug varchar(256),

    date date,

    conversion_id varchar(64),
    conversion_timestamp timestamp,

    account_id integer,
    campaign_id integer,
    ad_group_id integer,
    content_ad_id integer,
    source_id integer,

    touchpoint_id varchar(64),
    touchpoint_timestamp timestamp,
    conversion_lag integer
)
DISTSTYLE EVEN
SORTKEY (date);
