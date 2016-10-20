import backtosql
import io
import logging
import json
import os.path

from collections import defaultdict
from dateutil import rrule
from functools import partial
import unicodecsv as csv

from django.conf import settings

from utils import s3helpers

import dash.models
import dash.constants

from redshiftapi import db

from etl import models
from etl import helpers


logger = logging.getLogger(__name__)

MATERIALIZED_VIEWS_S3_PREFIX = 'materialized_views'
MATERIALIZED_VIEWS_FILENAME = 'view_{}.csv'

S3_FILE_URI = 's3://{bucket_name}/{key}'
CSV_DELIMITER = '\t'


def upload_csv(table_name, date, job_id, generator):
    logger.info('Create CSV for table "%s", job %s', table_name, job_id)
    s3_path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        table_name,
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME.format(job_id),
    )

    bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

    with io.BytesIO() as csvfile:
        writer = csv.writer(csvfile, dialect='excel', delimiter=CSV_DELIMITER)

        for line in generator():
            writer.writerow(line)

        bucket.put(s3_path, csvfile.getvalue())

    logger.info('CSV for table "%s", job %s uploaded', table_name, job_id)
    return s3_path


def prepare_copy_csv_query(s3_path, table_name):
    sql = backtosql.generate_sql('etl_copy_csv.sql', {
        'table': table_name,
    })

    s3_url = S3_FILE_URI.format(bucket_name=settings.S3_BUCKET_STATS, key=s3_path)

    if settings.AWS_ACCESS_KEY_ID is not None and settings.AWS_ACCESS_KEY_ID != '':
        credentials = helpers.get_aws_credentials_string(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
        )
    else:
        credentials = helpers.get_aws_credentials_from_role()

    return sql, {
        's3_url': s3_url,
        'credentials': credentials,
        'delimiter': CSV_DELIMITER,
    }


def prepare_daily_delete_query(table_name, date):
    sql = backtosql.generate_sql('etl_daily_delete.sql', {
        'table': table_name,
    })

    return sql, {
        'date': date,
    }


def prepare_date_range_delete_query(table_name, date_from, date_to):
    sql = backtosql.generate_sql('etl_delete.sql', {
        'table': table_name,
    })

    return sql, {
        'date_from': date_from,
        'date_to': date_to,
    }


class Materialize(object):

    TABLE_NAME = 'missing'
    IS_TEMPORARY_TABLE = False

    def __init__(self, job_id, date_from, date_to):
        self.job_id = job_id
        self.date_from = date_from
        self.date_to = date_to

    def generate(self, **kwargs):
        raise NotImplementedError()


class MVHelpersSource(Materialize):

    TABLE_NAME = 'mvh_source'
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        s3_path = upload_csv(
            self.TABLE_NAME,
            self.date_to,
            self.job_id,
            self.generate_rows
        )

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql('etl_create_temp_table_mvh_source.sql', None)
                c.execute(sql)

                logger.info('Copying CSV to table "%s", job %s', self.TABLE_NAME, self.job_id)
                sql, params = prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)

    def generate_rows(self):
        sources = dash.models.Source.objects.all().order_by('id')

        for source in sources:
            yield (
                source.id,
                helpers.extract_source_slug(source.bidder_slug),
                source.bidder_slug,
            )


class MVHelpersCampaignFactors(Materialize):
    """
    Helper view that puts campaign factors into redshift. Its than used to construct the mv_master view.
    """

    TABLE_NAME = 'mvh_campaign_factors'
    IS_TEMPORARY_TABLE = True

    def generate(self, campaign_factors, **kwargs):
        s3_path = upload_csv(
            self.TABLE_NAME,
            self.date_to,
            self.job_id,
            partial(self.generate_rows, campaign_factors)
        )

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql('etl_create_temp_table_mvh_campaign_factors.sql', None)
                c.execute(sql)

                logger.info('Copying CSV to table "%s", job %s', self.TABLE_NAME, self.job_id)
                sql, params = prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)

    def generate_rows(self, campaign_factors):
        for date, campaign_dict in campaign_factors.iteritems():
            for campaign, factors in campaign_dict.iteritems():
                yield (
                    date,
                    campaign.id,

                    factors[0],
                    factors[1],
                    factors[2],
                )


class MVHelpersAdGroupStructure(Materialize):
    """
    Helper view that puts ad group structure (campaign id, account id, agency id) into redshift. Its than
    used to construct the mv_master view.
    """

    TABLE_NAME = 'mvh_adgroup_structure'
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        s3_path = upload_csv(
            self.TABLE_NAME,
            self.date_to,
            self.job_id,
            self.generate_rows
        )

        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql('etl_create_temp_table_mvh_adgroup_structure.sql', None)
                c.execute(sql)

                logger.info('Copying CSV to table "%s", job %s', self.TABLE_NAME, self.job_id)
                sql, params = prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                c.execute(sql, params)

    def generate_rows(self):
        ad_groups = dash.models.AdGroup.objects.select_related('campaign', 'campaign__account').all()

        for ad_group in ad_groups:
            yield (
                ad_group.campaign.account.agency_id,
                ad_group.campaign.account_id,
                ad_group.campaign_id,
                ad_group.id,
            )


class MVHelpersNormalizedStats(Materialize):
    """
    Writes a temporary table that has data from stats transformed into the correct format for mv_master construction.
    It does conversion from age, gender etc. strings to constatnts, calculates nano, calculates effective cost
    and license fee based on mvh_campaign_factors.
    """

    TABLE_NAME = 'mvh_clean_stats'
    IS_TEMPORARY_TABLE = True

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                sql = backtosql.generate_sql('etl_create_temp_table_mvh_clean_stats.sql', None)
                c.execute(sql)

                logger.info('Running insert into table "%s", job %s', self.TABLE_NAME, self.job_id)
                sql, params = self.prepare_insert_query()
                c.execute(sql, params)

    def prepare_insert_query(self):
        params = helpers.get_local_multiday_date_context(self.date_from, self.date_to)

        sql = backtosql.generate_sql('etl_insert_mvh_clean_stats.sql', {
            'date_ranges': params.pop('date_ranges'),
        })

        return sql, params


class MasterView(Materialize):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data.

    NOTE: It excludes outbrain publishers as those are currently not linked to content ads and so
    breakdown by publisher and content ad is not possible for them.
    """

    TABLE_NAME = 'mv_master'
    POSTCLICK_STRUCTURE_BREAKDOWN_INDEX = 8

    def generate(self, **kwargs):
        self.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):

            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = prepare_daily_delete_query(self.TABLE_NAME, date)
                    c.execute(sql, params)

                    logger.info('Running insert traffic data into table "%s" for day %s, job %s',
                                self.TABLE_NAME, date, self.job_id)
                    sql, params = self.prepare_insert_traffic_data_query(date)
                    c.execute(sql, params)

                    # generate csv in transaction as it needs data created in it
                    s3_path = upload_csv(
                        self.TABLE_NAME,
                        date,
                        self.job_id,
                        partial(self.generate_rows, c, date)
                    )

                    logger.info('Copying CSV to table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

                    logger.info('Copying any diff data from mv_master_diff for day %s, job %s', date, self.job_id)
                    sql, params = self.prepare_copy_diff_data_query(c, date)
                    c.execute(sql, params)

    def generate_rows(self, cursor, date):
        for breakdown_key, row, _ in self.get_postclickstats(cursor, date):
            yield row

    def prepare_insert_traffic_data_query(self, date):
        sql = backtosql.generate_sql('etl_insert_mv_master_stats.sql', {})

        return sql, {
            'date': date,
        }

    def prefetch(self):
        self.ad_groups_map = {x.id: x for x in dash.models.AdGroup.objects.all()}
        self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.all()}
        self.accounts_map = {x.id: x for x in dash.models.Account.objects.all()}
        self.sources_slug_map = {
            helpers.extract_source_slug(x.bidder_slug): x for x in dash.models.Source.objects.all()}
        self.sources_map = {x.id: x for x in dash.models.Source.objects.all()}

    def get_postclickstats(self, cursor, date):

        # group postclick rows by ad group and postclick source
        rows_by_ad_group = defaultdict(lambda: defaultdict(list))
        for row in self.get_postclickstats_query_results(cursor, date):
            postclick_source = helpers.extract_postclick_source(row.postclick_source)
            rows_by_ad_group[row.ad_group_id][postclick_source].append(row)

        for ad_group_id, rows_by_postclick_source in rows_by_ad_group.iteritems():

            if len(rows_by_postclick_source.keys()) > 1:
                logger.info("Postclick stats for a single ad group (%s) from different sources %s, date %s",
                            ad_group_id, rows_by_postclick_source.keys(), date)

            rows = helpers.get_highest_priority_postclick_source(rows_by_postclick_source)

            for row in rows:
                source_slug = helpers.extract_source_slug(row.source_slug)
                if source_slug not in self.sources_slug_map:
                    logger.info("Got postclick stats for unknown source: %s", row.source_slug)
                    continue

                if row.ad_group_id not in self.ad_groups_map:
                    logger.info("Got postclick stats for unknown ad group: %s", row.ad_group_id)
                    continue

                source = self.sources_slug_map[source_slug]
                ad_group = self.ad_groups_map[row.ad_group_id]
                campaign = self.campaigns_map[ad_group.campaign_id]
                account = self.accounts_map[campaign.account_id]

                returning_users = helpers.calculate_returning_users(row.users, row.new_visits)

                yield (
                    helpers.get_breakdown_key_for_postclickstats(source.id, row.content_ad_id),
                    (
                        date,
                        source.id,

                        account.agency_id,
                        account.id,
                        campaign.id,
                        ad_group.id,
                        row.content_ad_id,
                        row.publisher,

                        dash.constants.DeviceType.UNDEFINED,
                        None,
                        None,
                        None,
                        dash.constants.AgeGroup.UNDEFINED,
                        dash.constants.Gender.UNDEFINED,
                        dash.constants.AgeGenderGroup.UNDEFINED,

                        0,
                        0,
                        0,
                        0,

                        row.visits,
                        row.new_visits,
                        row.bounced_visits,
                        row.pageviews,
                        row.total_time_on_site,

                        0,
                        0,
                        0,
                        0,

                        row.users,
                        returning_users,
                    ),
                    (row.conversions, row.postclick_source)
                )

    def get_postclickstats_query_results(self, c, date):
        sql, params = self.prepare_postclickstats_query(date)

        c.execute(sql, params)
        return db.xnamedtuplefetchall(c)

    def prepare_postclickstats_query(self, date):
        sql = backtosql.generate_sql('etl_breakdown_simple_one_day.sql', {
            'breakdown': models.K1PostclickStats().get_breakdown([
                'ad_group_id', 'postclick_source', 'content_ad_id', 'source_slug', 'publisher',
            ]),
            'aggregates': models.K1PostclickStats().get_aggregates(),
            'table': 'postclickstats'
        })
        params = {'date': date}

        return sql, params

    def prepare_copy_diff_data_query(self, cursor, date):
        sql = backtosql.generate_sql('etl_copy_diff_into_mv_master.sql', None)

        params = {'date': date}

        return sql, params


class MasterPublishersView(Materialize):

    TABLE_NAME = 'mv_pubs_master'

    def __init__(self, *args, **kwargs):
        self.outbrain = dash.models.Source.objects.get(name__iexact='outbrain')
        super(MasterPublishersView, self).__init__(*args, **kwargs)

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info('Deleting data from table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = prepare_date_range_delete_query(self.TABLE_NAME, self.date_from, self.date_to)
                c.execute(sql, params)

                logger.info('Creating temp table "mvh_ad_group_cpcs" for date range %s - %s, job %s',
                            self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_temp_table_ad_group_cpcs()
                c.execute(sql, params)

                logger.info('Inserting non-Outbrain data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_select_insert_mv_pubs_master()
                c.execute(sql, params)

                logger.info('Inserting Outbrain data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_select_insert_outbrain_to_mv_pubs_master()
                c.execute(sql, params)

    def prepare_temp_table_ad_group_cpcs(self):
        sql = backtosql.generate_sql('etl_create_temp_table_mvh_ad_group_cpcs.sql', None)
        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'source_name': self.outbrain.name,
        }

    def prepare_select_insert_mv_pubs_master(self):
        sql = backtosql.generate_sql('etl_select_insert_mv_pubs_master.sql', None)
        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }

    def prepare_select_insert_outbrain_to_mv_pubs_master(self):
        sql = backtosql.generate_sql('etl_select_insert_outbrain_to_mv_pubs_master.sql', {
            'source_id': self.outbrain.id,
        })
        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVConversions(Materialize):

    TABLE_NAME = 'mv_conversions'

    def __init__(self, *args, **kwargs):
        super(MVConversions, self).__init__(*args, **kwargs)
        self.master_view = MasterView(self.job_id, self.date_from, self.date_to)

    def generate(self, **kwargs):

        self.master_view.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = prepare_daily_delete_query(self.TABLE_NAME, date)
                    c.execute(sql, params)

                    # generate csv in transaction as it needs data created in it
                    s3_path = upload_csv(
                        self.TABLE_NAME,
                        date,
                        self.job_id,
                        partial(self.generate_rows, c, date)
                    )

                    logger.info('Copying CSV to table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = prepare_copy_csv_query(s3_path, self.TABLE_NAME)
                    c.execute(sql, params)

    def generate_rows(self, cursor, date):
        for breakdown_key, row, conversions_tuple in self.master_view.get_postclickstats(cursor, date):
            conversions = conversions_tuple[0]
            postclick_source = conversions_tuple[1]

            if conversions:
                conversions = json.loads(conversions)
                for slug, hits in conversions.iteritems():
                    slug = helpers.get_conversion_prefix(postclick_source, slug)
                    yield tuple(list(row)[:self.master_view.POSTCLICK_STRUCTURE_BREAKDOWN_INDEX] + [slug, hits])


class MVTouchpointConversions(Materialize):

    TABLE_NAME = 'mv_touchpointconversions'

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info('Deleting data from table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = prepare_date_range_delete_query(self.TABLE_NAME, self.date_from, self.date_to)
                c.execute(sql, params)

                logger.info('Inserting data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_insert_query()
                c.execute(sql, params)

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_insert_mv_touchpointconversions.sql', {})

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class DerivedMaterializedView(Materialize):
    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:

                logger.info('Deleting data from table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = prepare_date_range_delete_query(self.TABLE_NAME, self.date_from, self.date_to)
                c.execute(sql, params)

                logger.info('Inserting data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_insert_query()
                c.execute(sql, params)

    def prepare_insert_query(self):
        raise NotImplementedError()


class MVAccount(DerivedMaterializedView):

    TABLE_NAME = 'mv_account'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVCampaign.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVAccountDeliveryGeo(DerivedMaterializedView):

    TABLE_NAME = 'mv_account_delivery_geo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
                'country', 'state', 'dma',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVCampaignDeliveryGeo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVAccountDeliveryDemo(DerivedMaterializedView):

    TABLE_NAME = 'mv_account_delivery_demo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
                'device_type', 'age', 'gender', 'age_gender',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVCampaignDeliveryDemo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVCampaign(DerivedMaterializedView):

    TABLE_NAME = 'mv_campaign'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVAdGroup.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVCampaignDeliveryGeo(DerivedMaterializedView):

    TABLE_NAME = 'mv_campaign_delivery_geo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id',
                'country', 'state', 'dma',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVAdGroupDeliveryGeo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVCampaignDeliveryDemo(DerivedMaterializedView):

    TABLE_NAME = 'mv_campaign_delivery_demo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id',
                'device_type', 'age', 'gender', 'age_gender',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVAdGroupDeliveryDemo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVAdGroup(DerivedMaterializedView):

    TABLE_NAME = 'mv_ad_group'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': 'mv_content_ad',
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVAdGroupDeliveryGeo(DerivedMaterializedView):

    TABLE_NAME = 'mv_ad_group_delivery_geo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id',
                'country', 'state', 'dma',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVContentAdDeliveryGeo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVAdGroupDeliveryDemo(DerivedMaterializedView):

    TABLE_NAME = 'mv_ad_group_delivery_demo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id',
                'device_type', 'age', 'gender', 'age_gender',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVContentAdDeliveryDemo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVContentAd(DerivedMaterializedView):

    TABLE_NAME = 'mv_content_ad'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id', 'content_ad_id'
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MVContentAdDeliveryDemo.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVContentAdDeliveryGeo(DerivedMaterializedView):

    TABLE_NAME = 'mv_content_ad_delivery_geo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id', 'content_ad_id',
                'country', 'state', 'dma',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MasterView.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVContentAdDeliveryDemo(DerivedMaterializedView):

    TABLE_NAME = 'mv_content_ad_delivery_demo'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id', 'content_ad_id',
                'device_type', 'age', 'gender', 'age_gender',
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MasterView.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVTouchpointAccount(DerivedMaterializedView):

    TABLE_NAME = 'mv_touch_account'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_touchpointconversions.sql', {
            # use MVMaster model as it has same breakdown columns
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVTouchpointConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVTouchpointCampaign(DerivedMaterializedView):

    TABLE_NAME = 'mv_touch_campaign'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_touchpointconversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id',
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVTouchpointConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVTouchpointAdGroup(DerivedMaterializedView):

    TABLE_NAME = 'mv_touch_ad_group'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_touchpointconversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id',
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVTouchpointConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVTouchpointContentAd(DerivedMaterializedView):

    TABLE_NAME = 'mv_touch_content_ad'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_touchpointconversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id', 'content_ad_id'
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVTouchpointConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVConversionsAccount(DerivedMaterializedView):

    TABLE_NAME = 'mv_conversions_account'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_conversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id',
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVConversionsCampaign(DerivedMaterializedView):

    TABLE_NAME = 'mv_conversions_campaign'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_conversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id',
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVConversionsAdGroup(DerivedMaterializedView):

    TABLE_NAME = 'mv_conversions_ad_group'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_conversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id',
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVConversionsContentAd(DerivedMaterializedView):

    TABLE_NAME = 'mv_conversions_content_ad'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert_conversions.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id', 'content_ad_id'
            ]),
            'destination_table': self.TABLE_NAME,
            'source_table': MVConversions.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }


class MVPublishersAdGroup(DerivedMaterializedView):

    TABLE_NAME = 'mv_pubs_ad_group'

    def prepare_insert_query(self):
        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': models.MVMaster().get_breakdown([
                'date', 'source_id', 'agency_id', 'account_id', 'campaign_id', 'ad_group_id', 'publisher', 'external_id'
            ]),
            'aggregates': models.MVMaster().get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': MasterPublishersView.TABLE_NAME,
        })

        return sql, {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
