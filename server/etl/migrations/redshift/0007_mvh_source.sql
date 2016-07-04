CREATE TABLE mvh_source (
       source_id int2 encode bytedict,
       bidder_slug varchar(127) encode lzo,
       clean_slug varchar(127) encode lzo
) sortkey(bidder_slug);
