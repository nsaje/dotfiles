CREATE TABLE touchpointconversions (
    zuid varchar(36),
    date timestamp,

    conversion_id integer,
    conversion_slug varchar(256),
    conversion_ts timestamp,

    redirect_ts timestamp,
    t_diff integer,

    account_id integer,
    campaign_id integer,
    ad_group_id integer,
    cotnent_ad_id integer,
    source_id integer,
)
DISTSTYLE EVEN
SORTKEY (date);
