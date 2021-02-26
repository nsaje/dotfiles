CREATE TEMP TABLE mvh_source (
    source_id int2 encode AZ64,
    bidder_slug varchar(127) encode zstd,
    clean_slug varchar(127) encode zstd,
    parent_source_id int2 encode AZ64
)
diststyle all
sortkey(bidder_slug)
