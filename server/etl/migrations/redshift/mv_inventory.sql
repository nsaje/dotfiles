CREATE TABLE mv_inventory (
    country varchar(2) encode zstd,
    publisher varchar(255) encode zstd,
    device_type int2 encode zstd,
    source_id int2 encode zstd,

    bid_reqs bigint encode zstd,
    bids bigint encode zstd,
    win_notices bigint encode zstd,
    total_win_price real encode zstd,
    slots bigint encode zstd,
    redirects bigint encode zstd
) interleaved sortkey(country, publisher, device_type);
