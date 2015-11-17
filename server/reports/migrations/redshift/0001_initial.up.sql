CREATE TABLE contentadstats (
    id integer IDENTITY PRIMARY KEY,
    date date,
    content_ad_id integer,
    adgroup_id integer,
    source_id integer,
    campaign_id integer,
    account_id integer,

    impressions integer,
    clicks integer,
    cost_cc integer,
    data_cost_cc integer,

    visits integer,
    new_visits integer,
    bounced_visits integer,
    pageviews integer,
    total_time_on_site integer,

    conversions varchar(512)
)
DISTSTYLE EVEN
SORTKEY (date);
