# Zemanta Eins - ETL #

## Preparing the master view ##

Master view `mv_master` holds the whole breakdown, so whatever breakdown we want we only need to query
this table. All the data in it is cleaned and transformed in advance so that we don't need to deal with
this operations when we query.

Transforming of data includes:

A. applying cost factors that are calculated from daily statements to `cost`, `data_cost` and so calculating `effective_cost_nano`, `effective_data_cost_nano` and `license_fee_nano`

B. transforming UTC `date` and `hour` fields to local (EST) day `date`

C. transforming source slugs to `source_id`

D. adding `campaign_id`, `account_id`, `agency_id` fields based on `ad_group_id`

E. transforming `device_type`, `country`, `dma`, `state`, `age`, `gender` and `age_gender` to constants used by z1

F. converting `spend` and `data_spend` to `cost_nano` and `data_cost_nano`

Most of transformations are made directly in the database so that we don't have the overhead of python,
download and upload of data.

### The procedure ###

First we prepare helper materialized view, which we than join into mv_master.

#### 1. Prepare helper materialized views ####

Helper materialized views tables are dropped and created for each refresh.
Because of this table create scripts reside in `etl/templates` and are named `etl_create_table*`

1. calculate effective cost factors in `daily_statements` and
   execute `MVHelpersCampaignFactors` materialization that writes them to database (needed for step A).
   This produces table `mvh_campaign_factors`.
2. write ad group structure `MVHelpersAdGroupStructure` to provide data for step D in database.
   This produces table `mvh_adgroup_structure`.
3. write `MVHelpersSource` that provides mapping between source slug and source id
   This produces table `mvh_source`.

#### 2. Join data to mv_master ####

View that takes care of the joining is `MVMaster` and creates the `mv_master` table.

We join helper materialized views and results from a subquery in which we perform steps B and E into `mv_master`
as seen in `etl/templates/etl_insert_mv_master_stats`.
Than we add postclick data to it in python - this data is small enough that this step does not have a
big performance hit.

### Other notes ###

Currently first 3 materialized views are there to support legacy tables: `ContentAdStats`, `Publishers`, `TouchpointConversions`. `MVMaster` is basically extended `ContentAdStats`, same logics but lots of it is happening in database as it is broader and more resource intensive.

## Code structure ##

Base folder: `etl`

- `refresh` :: entry point, runs the listed materialized views. Its run every hour at 25 minutes past (see `crontab.txt`)
- `materialize` :: new materialized views
- `helpers` :: clean and transform data helpers
- `migrations/redshift/..` :: permanent redshift tables
- `migrations/redshift/0006_udf_functions.sql` :: UDF python functions that are used to clean data in database.
   Should be applied to redshift if changed.
- `templates/` :: templates used in materialization, this is where `backtosql` is searching for them.

Whenever we use `backtosql` that means we ar going to load a sql template file from `etl/templates/` with the
same name.

## Known errors ##

Conversions and touchpointconversions are removed temporarily as they take too much of disk space.


## Derived views ##

After we prepare derived views we construct deriver materialized views. Derived views are preaggregated
breakdowns - basically just provide a sub breakdown. The are intended to reduce data needed to be queried to
get a breakdown. Example:

```
Origin table mv_imaginary_master:
Ad group|content ad|clicks

Derived view mv_imaginary_ad_group:
Ad group|clicks

Example sql:

insert into mv_imaginary_ad_group
select ad_group_id, sum(clicks) from mv_imaginary_master;
```

Currently supported derived views: `MVCampaign`, `MVCampaignDelivery`, `MVAccount`, `MVAccountDelivery`, `MVAdGroup`, `MVAdGroupDelivery`, `MVContentAd`, `MVContentAdDelivery`.

To see their definition check `migrations/redshift/000X_account/campaign_(delivery).sql`

NOTE: All materialized views include `source_id` and `date` breakdowns. This is because we
always query based on these two attributes. `source_id` is taken from filter. That is why they
should also always be in sortkey.

Intention of these derived views is if we need to query breakdown `campaign, source` we do not need
to query `mv_master` but the minimum derived view that has this breakdown available - `mv_campaign`
in our case. To see the selection of views check `redshiftapi/models.py::get_best_view` and its
matching test in `redshiftapi/tests/test_models.py::test_get_best_view`.
