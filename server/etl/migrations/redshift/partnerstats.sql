CREATE TABLE partnerstats (
       date date encode AZ64,
       utc_date date encode AZ64,
       utc_hour integer encode AZ64,
       exchange varchar(127) encode zstd,
       outbrain_section_id varchar(127) encode zstd default NULL,
       outbrain_publisher_id varchar(127) encode zstd default NULL,
       publisher varchar(255) encode zstd,

       impressions integer encode zstd,
       clicks integer encode zstd,
       cost_nano bigint encode zstd,
       original_cost_nano bigint encode zstd,
       ssp_cost_nano bigint encode zstd
)
DISTSTYLE EVEN
COMPOUND SORTKEY (date);
