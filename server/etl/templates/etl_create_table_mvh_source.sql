CREATE TABLE mvh_source (
       source_id int2 encode bytedict,
       slug varchar(127) encode lzo
) sortkey(slug);