CREATE TABLE touchpointconversions (
    zuid varchar(36),
    slug varchar(256),

    date timestamp,

    conversion_id integer,
    conversion_ts timestamp,

    redirect_ts timestamp,
    t_diff integer,

    account_id integer,
    campaign_id integer,
    ad_group_id integer,
    content_ad_id integer,
    source_id integer,
)
DISTSTYLE EVEN
SORTKEY (date);
