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
from django.utils.functional import cached_property

from utils import s3helpers
from utils import threads

import dash.models
import dash.constants

from redshiftapi import db

import models
import helpers
import derived_views


logger = logging.getLogger(__name__)

MATERIALIZED_VIEWS_S3_PREFIX = 'materialized_views'
MATERIALIZED_VIEWS_FILENAME = '{}_{}.csv'

S3_FILE_URI = 's3://{bucket_name}/{key}'
CSV_DELIMITER = '\t'

"""
NOTE: Some of the views in the master views rely on having campaign factors
available for the whole range.
"""


def _do_upload_csv(s3_path, generator):
    bucket = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_STATS)

    with io.BytesIO() as csvfile:
        writer = csv.writer(csvfile, dialect='excel', delimiter=CSV_DELIMITER)

        for line in generator():
            writer.writerow(line)

        bucket.put(s3_path, csvfile.getvalue())


def upload_csv_async(table_name, date, job_id, generator):
    logger.info('Create async CSV for table "%s", job %s', table_name, job_id)
    s3_path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        table_name,
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME.format(table_name, job_id),
    )

    t = threads.AsyncFunction(partial(_do_upload_csv, s3_path, generator))
    t.start()

    return t, s3_path


def upload_csv(table_name, date, job_id, generator):
    logger.info('Create CSV for table "%s", job %s', table_name, job_id)
    s3_path = os.path.join(
        MATERIALIZED_VIEWS_S3_PREFIX,
        table_name,
        date.strftime("%Y/%m/%d/"),
        MATERIALIZED_VIEWS_FILENAME.format(table_name, job_id),
    )

    _do_upload_csv(s3_path, generator)
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


def prepare_daily_delete_query(table_name, date, account_id):
    sql = backtosql.generate_sql('etl_daily_delete.sql', {
        'table': table_name,
        'account_id': account_id,
    })

    params = {
        'date': date,
    }

    if account_id:
        params['account_id'] = account_id

    return sql, params


def prepare_date_range_delete_query(table_name, date_from, date_to, account_id):
    sql = backtosql.generate_sql('etl_delete.sql', {
        'table': table_name,
        'account_id': account_id,
    })

    params = {
        'date_from': date_from,
        'date_to': date_to,
    }

    if account_id:
        params['account_id'] = account_id

    return sql, params


def get_ad_group_ids_or_none(account_id):
    """ Some tables only have ad group ids, returns ad group ids if account_id is passed """

    if not account_id:
        return None

    return list(dash.models.AdGroup.objects.filter(campaign__account_id=account_id).values_list('pk', flat=True))


def get_outbrain():
    return dash.models.Source.objects.get(name__iexact='outbrain')


def get_yahoo():
    return dash.models.Source.objects.get(name__iexact='yahoo')


class Materialize(object):

    TABLE_NAME = 'missing'
    IS_TEMPORARY_TABLE = False
    IS_DERIVED_VIEW = False

    def __init__(self, job_id, date_from, date_to, account_id):
        self.job_id = job_id
        self.date_from = date_from
        self.date_to = date_to
        self.account_id = account_id

    def generate(self, **kwargs):
        raise NotImplementedError()

    def _add_account_id_param(self, params):
        if self.account_id:
            params['account_id'] = self.account_id

        return params

    def _add_ad_group_id_param(self, params):
        if self.account_id:
            params['ad_group_id'] = get_ad_group_ids_or_none(self.account_id)

        return params


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
                logger.info('Copied CSV to table "%s", job %s', self.TABLE_NAME, self.job_id)

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
    Helper view that puts campaign factors into redshift. Its then used to construct the mv_master view.
    """

    TABLE_NAME = 'mvh_campaign_factors'
    IS_TEMPORARY_TABLE = True

    def generate(self, campaign_factors, **kwargs):
        self.check_date_range_continuation(campaign_factors)

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
                logger.info('Copied CSV to table "%s", job %s', self.TABLE_NAME, self.job_id)

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

    def check_date_range_continuation(self, campaign_factors):
        # checks that all the dates withing the reprocessed date range have campaign factors set
        for dt in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            dt = dt.date()
            if dt not in campaign_factors:
                raise Exception('Campaign factors missing for the date %s within date range %s - %s, job %s',
                                dt, self.date_from, self.date_to, self.job_id)


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
                logger.info('Copied CSV to table "%s", job %s', self.TABLE_NAME, self.job_id)

    def generate_rows(self):
        ad_groups = dash.models.AdGroup.objects.select_related('campaign', 'campaign__account').all()
        if self.account_id:
            ad_groups = ad_groups.filter(campaign__account_id=self.account_id)

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
                logger.info('Done insert into table "%s", job %s', self.TABLE_NAME, self.job_id)

    def prepare_insert_query(self):
        yahoo = get_yahoo()
        params = helpers.get_local_multiday_date_context(self.date_from, self.date_to)

        sql = backtosql.generate_sql('etl_insert_mvh_clean_stats.sql', {
            'date_ranges': params.pop('date_ranges'),
            'account_id': self.account_id,
            'yahoo_slug': yahoo.bidder_slug,
        })

        return sql, self._add_ad_group_id_param(params)


class MasterView(Materialize):
    """
    Represents breakdown by all dimensions available. It containts traffic, postclick, conversions
    and tochpoint conversions data.

    NOTE: It excludes outbrain publishers as those are currently not linked to content ads and so
    breakdown by publisher and content ad is not possible for them.
    """

    TABLE_NAME = 'mv_master'

    def generate(self, **kwargs):
        self.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):

            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = prepare_daily_delete_query(self.TABLE_NAME, date, self.account_id)
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
        for _, row, _ in self.get_postclickstats(cursor, date):
            yield row

    def prepare_insert_traffic_data_query(self, date):
        sql = backtosql.generate_sql('etl_insert_mv_master_stats.sql', {
            'account_id': self.account_id,
        })

        return sql, self._add_account_id_param({
            'date': date,
        })

    def prefetch(self):
        if self.account_id:
            self.ad_groups_map = {x.id: x for x in dash.models.AdGroup.objects.filter(
                campaign__account_id=self.account_id)}
            self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.filter(account_id=self.account_id)}
            self.accounts_map = {x.id: x for x in dash.models.Account.objects.filter(id=self.account_id)}

        else:
            self.ad_groups_map = {x.id: x for x in dash.models.AdGroup.objects.all()}
            self.campaigns_map = {x.id: x for x in dash.models.Campaign.objects.all()}
            self.accounts_map = {x.id: x for x in dash.models.Account.objects.all()}

        self.sources_slug_map = {
            helpers.extract_source_slug(x.bidder_slug): x for x in dash.models.Source.objects.all()}
        self.sources_map = {x.id: x for x in dash.models.Source.objects.all()}
        self.outbrain = get_outbrain()
        self.yahoo = get_yahoo()

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

                publisher = row.publisher
                if source.id == self.yahoo.id:
                    publisher = 'all publishers'
                elif publisher and source.id != self.outbrain.id:
                    publisher = publisher.lower()

                yield (
                    helpers.get_breakdown_key_for_postclickstats(source.id, row.content_ad_id),
                    (
                        date,
                        source.id,

                        account.id,
                        campaign.id,
                        ad_group.id,
                        row.content_ad_id,
                        publisher,
                        u'{}__{}'.format(publisher if publisher else u'', source.id),  # publisher_source_id

                        dash.constants.DeviceType.UNKNOWN,
                        None,  # device_os
                        None,  # device_os_version
                        dash.constants.PlacementMedium.UNKNOWN,

                        dash.constants.PlacementType.UNKNOWN,
                        dash.constants.VideoPlaybackMethod.UNKNOWN,

                        None,  # country
                        None,  # state
                        None,  # dma
                        None,  # city_id

                        dash.constants.Age.UNDEFINED,
                        dash.constants.Gender.UNDEFINED,
                        dash.constants.AgeGender.UNDEFINED,

                        0,  # impressions
                        0,  # clicks
                        0,  # cost_nano
                        0,  # data_cost_nano

                        row.visits,
                        row.new_visits,
                        row.bounced_visits,
                        row.pageviews,
                        row.total_time_on_site,

                        0,  # effective_cost_nano
                        0,  # effective_data_cost_nano
                        0,  # license_fee_nano
                        0,  # margin_nano

                        row.users,
                        returning_users,

                        None,  # video_start
                        None,  # video_first_quartile
                        None,  # video_midpoint
                        None,  # video_third_quartile
                        None,  # video_complete
                        None,  # video_progress_3s

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
            'table': 'postclickstats',
            'account_id': self.account_id,
        })

        return sql, self._add_ad_group_id_param({'date': date})

    def prepare_copy_diff_data_query(self, cursor, date):
        sql = backtosql.generate_sql('etl_copy_diff_into_mv_master.sql', {
            'account_id': self.account_id,
        })

        return sql, self._add_account_id_param({'date': date})


class MasterPublishersView(Materialize):

    TABLE_NAME = 'mv_master_pubs'

    def __init__(self, *args, **kwargs):
        self.outbrain = get_outbrain()
        self.yahoo = get_yahoo()
        super(MasterPublishersView, self).__init__(*args, **kwargs)

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info('Deleting data from table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = prepare_date_range_delete_query(self.TABLE_NAME, self.date_from, self.date_to,
                                                              self.account_id)
                c.execute(sql, params)

                logger.info('Inserting non-Outbrain data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_select_insert_mv_master_pubs()
                c.execute(sql, params)

                logger.info('Inserting Outbrain data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_select_insert_outbrain_to_mv_master_pubs()
                c.execute(sql, params)

    def prepare_select_insert_mv_master_pubs(self):
        sql = backtosql.generate_sql('etl_select_insert_mv_pubs_master.sql', {
            'account_id': self.account_id,
        })

        return sql, self._add_account_id_param({
            'date_from': self.date_from,
            'date_to': self.date_to,
        })

    def prepare_select_insert_outbrain_to_mv_master_pubs(self):
        sql = backtosql.generate_sql('etl_select_insert_outbrain_to_mv_pubs_master.sql', {
            'source_id': self.outbrain.id,
            'account_id': self.account_id,
        })

        return sql, self._add_ad_group_id_param({
            'date_from': self.date_from,
            'date_to': self.date_to,
        })


class MVConversions(Materialize):

    TABLE_NAME = 'mv_conversions'

    def __init__(self, *args, **kwargs):
        super(MVConversions, self).__init__(*args, **kwargs)

        self.master_view = MasterView(self.job_id, self.date_from, self.date_to, self.account_id)

    def generate(self, **kwargs):

        self.master_view.prefetch()

        for date in rrule.rrule(rrule.DAILY, dtstart=self.date_from, until=self.date_to):
            date = date.date()

            with db.get_write_stats_transaction():
                with db.get_write_stats_cursor() as c:
                    logger.info('Deleting data from table "%s" for day %s, job %s', self.TABLE_NAME, date, self.job_id)
                    sql, params = prepare_daily_delete_query(self.TABLE_NAME, date, self.account_id)
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
        for _, row, conversions_tuple in self.master_view.get_postclickstats(cursor, date):
            conversions = conversions_tuple[0]
            postclick_source = conversions_tuple[1]

            if conversions:
                conversions = json.loads(conversions)

                for slug, hits in conversions.iteritems():
                    slug = helpers.get_conversion_prefix(postclick_source, slug)
                    yield tuple(list(row)[:8] + [slug, hits])


class MVTouchpointConversions(Materialize):

    TABLE_NAME = 'mv_touchpointconversions'

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:
                logger.info('Deleting data from table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = prepare_date_range_delete_query(self.TABLE_NAME, self.date_from,
                                                              self.date_to, self.account_id)
                c.execute(sql, params)

                logger.info('Inserting data into table "%s" for date range %s - %s, job %s',
                            self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                sql, params = self.prepare_insert_query()
                c.execute(sql, params)

    def prepare_insert_query(self):
        outbrain = get_outbrain()
        yahoo = get_yahoo()
        sql = backtosql.generate_sql('etl_insert_mv_touchpointconversions.sql', {
            'account_id': self.account_id,
            'outbrain_id': outbrain.id,
            'yahoo_id': yahoo.id,
        })

        return sql, self._add_account_id_param({
            'date_from': self.date_from,
            'date_to': self.date_to,
        })


class MasterDerivedView(Materialize):
    SOURCE_VIEW = MasterView.TABLE_NAME
    TEMPLATE = 'etl/migrations/redshift/mv_master.sql'
    IS_TEMPORARY_TABLE = False
    IS_DERIVED_VIEW = True

    @classmethod
    def create(cls, table_name, breakdown, sortkey, distkey=None, diststyle='key'):
        class Derived(cls):
            TABLE_NAME = table_name
            BREAKDOWN = breakdown
            SORTKEY = sortkey
            DISTKEY = distkey
            DISTSTYLE = diststyle

        return Derived

    @cached_property
    def model(self):
        return models.MVMaster()

    def generate(self, **kwargs):
        with db.get_write_stats_transaction():
            with db.get_write_stats_cursor() as c:

                logger.info('Create materialized view table if not exists "%s" for breakdown "%s", job %s', self.TABLE_NAME, self.BREAKDOWN, self.job_id)  # noqa
                sql = self.prepare_create_table()
                c.execute(sql)

                c.execute("SELECT count(1) FROM {}".format(self.TABLE_NAME))
                count = c.fetchone()[0]

                if not count:
                    logger.info('Fill empty materialized view "%s" for breakdown "%s" for full date range, job %s', self.TABLE_NAME, self.BREAKDOWN, self.job_id)  # noqa
                    sql, params = self.prepare_insert_query(None, None)
                    c.execute(sql, params)
                else:
                    logger.info('Deleting data from table "%s" for date range %s - %s, job %s',
                                self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                    sql, params = prepare_date_range_delete_query(self.TABLE_NAME, self.date_from,
                                                                  self.date_to, self.account_id)
                    c.execute(sql, params)

                    logger.info('Inserting data into table "%s" for date range %s - %s, job %s',
                                self.TABLE_NAME, self.date_from, self.date_to, self.job_id)
                    sql, params = self.prepare_insert_query(self.date_from, self.date_to)
                    c.execute(sql, params)

    def prepare_create_table(cls):
        with open(cls.TEMPLATE) as rs:
            sql = derived_views.generate_table_definition(
                cls.TABLE_NAME, rs, cls.BREAKDOWN, cls.SORTKEY, distkey=cls.DISTKEY, diststyle=cls.DISTSTYLE)
        return sql

    def prepare_insert_query(self, date_from, date_to):
        constraints = {}
        if date_from:
            constraints['date__gte'] = date_from

        if date_to:
            constraints['date__lte'] = date_to

        # if date range is not defined reprocess for all accounts as the table was just created
        if date_from and date_to:
            constraints = self._add_account_id_param(constraints)

        constraints = backtosql.Q(self.model, **constraints)

        sql = backtosql.generate_sql('etl_select_insert.sql', {
            'breakdown': self.model.get_breakdown(self.BREAKDOWN),
            'aggregates': self.model.get_ordered_aggregates(),
            'destination_table': self.TABLE_NAME,
            'source_table': self.SOURCE_VIEW,
            'constraints': constraints,
            'order': self.model.select_columns(subset=self.SORTKEY),
        })

        return sql, constraints.get_params()


class MasterPublishersDerivedView(MasterDerivedView):
    SOURCE_VIEW = MasterPublishersView.TABLE_NAME
    TEMPLATE = 'etl/migrations/redshift/mv_publishers_master.sql'

    @cached_property
    def model(self):
        return models.MVPublishers()


class ConversionsDerivedView(MasterDerivedView):
    SOURCE_VIEW = MVConversions.TABLE_NAME
    TEMPLATE = 'etl/migrations/redshift/mv_conversions.sql'

    @cached_property
    def model(self):
        return models.MVConversions()


class TouchpointConversionsDerivedView(MasterDerivedView):
    SOURCE_VIEW = MVTouchpointConversions.TABLE_NAME
    TEMPLATE = 'etl/migrations/redshift/mv_touchpointconversions.sql'

    @cached_property
    def model(self):
        return models.MVTouchpointConversions()
