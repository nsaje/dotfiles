# How to change table definitions #

To make changes to existing tables you need to create new tables with new definitions and copy the data over to them. Then you rename new tables to old names and drop the old tables. 

You will need to execute this migration manually in redshift console.

1. Make needed changes to the existing table in the "migration" files, eg `0001_mv_master.sql` and commit.
2. Create a copy of the table in a new table that has the new definition. 
   The new tables name should end with suffix `_new`, eg. `mv_master_new`.
3. Copy the data from the old table to new one.
4. Switch names, make the following in transaction: 
   - Rename the old table to *old* (add suffix `_old`). Eg.: `mv_master` is renamed to `mv_master_old.`
   - Rename the new table to the original name (remove suffix `_new`). Eg. `mv_master_new` is renamed to `mv_master`.
5. Drop the table ending with `_old`.
6. Alter owner of the table if you were using another username (eg. admin).

The whole procedure in sql:

```sql
-- CREATE TABLE mv_ad_group_new  *** new definition ***

insert into mv_ad_group_new (select * from mv_ad_group);  -- copy data over

-- switch names
begin;
alter table mv_ad_group rename to mv_ad_group_old;
alter table mv_ad_group_new rename to mv_ad_group;
commit;

-- drop old table
drop table mv_ad_group_old;

-- in case you were working with some other username
alter table mv_ad_group owner to eins2;
```
