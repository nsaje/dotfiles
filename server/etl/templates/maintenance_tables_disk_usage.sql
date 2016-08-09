-- source: http://stackoverflow.com/questions/21767780/how-to-find-size-of-database-schema-table-in-redshift
select
    trim(pgdb.datname) as Database,
    trim(a.name) as Table,
    ((b.mbytes/part.total::decimal)*100)::decimal(5,2) as pct_of_total,
    b.mbytes,
    b.unsorted_mbytes,
    a.rows
from stv_tbl_perm a
join pg_database as pgdb on pgdb.oid = a.db_id
join (
     select
          tbl,
          sum(decode(unsorted, 1, 1, 0)) as unsorted_mbytes,
          count(*) as mbytes
     from stv_blocklist
     group by tbl
) b on a.id=b.tbl
join (
     select sum(capacity) as  total
     from stv_partitions where part_begin=0
) as part on 1=1
where a.slice=0
order by 1, 3 desc, db_id, name;