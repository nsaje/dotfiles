import abc
import datetime
import logging
import random
import string
import unicodecsv
import StringIO
import os.path

import influx

from django.conf import settings

import dash.constants
import dash.views.helpers
import dash.models

from server import celery
from celery.exceptions import SoftTimeLimitExceeded

import stats.constants
import stats.api_breakdowns
import stats.api_reports

import utils.s3helpers
import utils.email_helper
import utils.columns
import utils.sort_helper
import utils.dates_helper
from utils import threads

import constants
import helpers
from reportjob import ReportJob


logger = logging.getLogger(__name__)

BATCH_ROWS = 10000


def create_job(user, query, scheduled_report=None):
    job = ReportJob(user=user, query=query, scheduled_report=scheduled_report)
    job.save()

    if settings.USE_CELERY_FOR_REPORTS:
        execute.delay(job.id)
    else:
        executor = ReportJobExecutor(job)
        thread = threads.AsyncFunction(executor.execute)
        thread.start()

    return job


@celery.app.task(acks_late=True, name='reports_execute', soft_time_limit=30 * 60)
def execute(job_id):
    logger.info('Start job executor for report id: %d', job_id)
    job = ReportJob.objects.get(pk=job_id)
    executor = ReportJobExecutor(job)
    executor.execute()
    logger.info('Done job executor for report id: %d', job_id)


class JobExecutor(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, job):
        self.job = job

    @abc.abstractmethod
    def execute(self):
        return


class MockJobExecutor(JobExecutor):

    def execute(self):
        pass


class ReportJobExecutor(JobExecutor):

    @influx.timer('dash.reports.execute')
    def execute(self):
        if self.job.status != constants.ReportJobStatus.IN_PROGRESS:
            logger.info('Running report job in incorrect state: %s' % self.job.status)
            influx.incr('dash.reports', 1, status='incorrect_state')
            return

        job_age = utils.dates_helper.utc_now() - self.job.created_dt
        if job_age > datetime.timedelta(hours=1):
            logger.info('Running too old report job: %s' % job_age)
            self._fail('too_old', 'Too old')
            return

        try:
            csv_report, filename = self.get_report(self.job)

            report_path = self.save_to_s3(csv_report, filename)
            self.send_by_email(self.job, report_path)

            self.job.result = report_path
            self.job.status = constants.ReportJobStatus.DONE
            influx.incr('dash.reports', 1, status='success')
            self.job.save()
        except SoftTimeLimitExceeded:
            self._fail('timeout', 'Timeout')
        except Exception as e:
            self._fail('failed', str(e))
            logger.exception('Exception when processing API report job %s' % self.job.id)

    def _fail(self, status, result):
        self.job.status = constants.ReportJobStatus.FAILED
        self.job.result = result
        influx.incr('dash.reports', 1, status=status)
        self.job.save()
        self._send_fail()

    def _send_fail(self):
        if len(self.job.query['options']['recipients']) <= 0:
            return

        if self.job.scheduled_report:
            return

        filter_constraints = helpers.get_filter_constraints(self.job.query['filters'])

        filtered_sources = []
        if filter_constraints.get('sources'):
            filtered_sources = dash.views.helpers.get_filtered_sources(self.job.user, ','.join(filter_constraints.get('sources', [])))

        view, breakdowns = self._extract_view_breakdown(self.job)
        ad_group_name, campaign_name, account_name = self._extract_entity_names(self.job.user, filter_constraints)

        utils.email_helper.send_async_report_fail(
            user=self.job.user,
            recipients=self.job.query['options']['recipients'],
            start_date=filter_constraints['start_date'],
            end_date=filter_constraints['end_date'],
            filtered_sources=filtered_sources,
            show_archived=self.job.query['options']['show_archived'],
            show_blacklisted_publishers=self.job.query['options']['show_blacklisted_publishers'],
            view=view,
            breakdowns=breakdowns,
            columns=self._extract_column_names(self.job.query['fields']),
            include_totals=self.job.query['options']['include_totals'],
            ad_group_name=ad_group_name,
            campaign_name=campaign_name,
            account_name=account_name,
        )

    @classmethod
    def get_report(cls, job):
        user = job.user

        filter_constraints = helpers.get_filter_constraints(job.query['filters'])
        start_date = filter_constraints['start_date']
        end_date = filter_constraints['end_date']
        filtered_sources = dash.views.helpers.get_filtered_sources(user, ','.join(filter_constraints.get('sources', [])))
        filtered_account_types = dash.views.helpers.get_filtered_account_types(filter_constraints.get('account_types', []))
        filtered_agencies = dash.views.helpers.get_filtered_agencies(filter_constraints.get('agencies', []))

        level = helpers.get_level_from_constraints(filter_constraints)
        breakdown = list(helpers.get_breakdown_from_fields(job.query['fields'], level))
        structure_constraints = cls._extract_structure_constraints(filter_constraints)

        constraints = stats.api_reports.prepare_constraints(
            user, breakdown, start_date, end_date, filtered_sources,
            show_archived=job.query['options']['show_archived'],
            show_blacklisted_publishers=job.query['options']['show_blacklisted_publishers'],
            filtered_account_types=filtered_account_types,
            filtered_agencies=filtered_agencies,
            only_used_sources=True,
            **structure_constraints
        )
        goals = stats.api_reports.get_goals(constraints, breakdown)

        field_name_mapping = utils.columns.get_field_names_mapping(
            goals.pixels, goals.conversion_goals,
            show_publishers_fields=stats.constants.PUBLISHER in breakdown
        )

        order = cls._get_order(job, field_name_mapping)
        column_names = cls._extract_column_names(job.query['fields'])
        columns = [field_name_mapping[column_name] for column_name in column_names]

        output = StringIO.StringIO()
        dashapi_cache = {}

        offset = 0
        while 1:
            rows = stats.api_reports.query(
                user=user,
                breakdown=breakdown,
                constraints=constraints,
                goals=goals,
                order=order,
                offset=offset,
                limit=BATCH_ROWS,
                level=level,
                columns=columns,
                include_items_with_no_spend=job.query['options']['include_items_with_no_spend'],
                dashapi_cache=dashapi_cache,
            )

            cls.convert_to_csv(job, rows, field_name_mapping, output, header=offset == 0)

            if len(rows) < BATCH_ROWS:
                break

            offset += BATCH_ROWS

        if job.query['options']['include_totals']:
            totals_constraints = stats.api_reports.prepare_constraints(
                user, breakdown, start_date, end_date, filtered_sources,
                show_archived=True,
                show_blacklisted_publishers=job.query['options']['show_blacklisted_publishers'],
                filtered_account_types=filtered_account_types,
                filtered_agencies=filtered_agencies,
                only_used_sources=True,
                **structure_constraints
            )
            totals = stats.api_reports.totals(
                user, helpers.limit_breakdown_to_level(breakdown, level),
                totals_constraints, goals, level, columns)

            cls.convert_to_csv(job, [totals], field_name_mapping, output, header=False)

        output.seek(0)

        return output, stats.api_reports.get_filename(breakdown, constraints)

    @classmethod
    def convert_to_csv(cls, job, data, field_name_mapping, output, header=True):
        requested_columns = cls._extract_column_names(job.query['fields'])

        csv_column_names = requested_columns
        original_to_dated = {k: k for k in requested_columns}
        if job.query['options']['show_status_date']:
            csv_column_names, original_to_dated = cls._date_column_names(csv_column_names)

        writer = unicodecsv.DictWriter(output, csv_column_names, encoding='utf-8', dialect='excel',
                                       quoting=unicodecsv.QUOTE_ALL)
        if header:
            writer.writeheader()
        for row in data:
            csv_row = {}
            for column_name in requested_columns:
                field_name = field_name_mapping[column_name]
                csv_column = original_to_dated[column_name]
                if field_name in row:
                    csv_row[csv_column] = row[field_name]
                else:
                    csv_row[csv_column] = ''
            writer.writerow(csv_row)

    @staticmethod
    def _extract_column_names(fields_list):
        fieldnames = []

        # extract unique field names
        for field in fields_list:
            field = field['field']
            if field not in fieldnames:
                fieldnames.append(field)

        return fieldnames

    @classmethod
    def save_to_s3(cls, csv, human_readable_filename):
        filename = cls._generate_random_filename()
        human_readable_filename = human_readable_filename + '.csv' if human_readable_filename else None
        utils.s3helpers.S3Helper(settings.RESTAPI_REPORTS_BUCKET).put_file(filename, csv, human_readable_filename)
        return os.path.join(settings.RESTAPI_REPORTS_URL, filename)

    @classmethod
    def send_by_email(cls, job, report_path):
        if len(job.query['options']['recipients']) <= 0:
            return

        filter_constraints = helpers.get_filter_constraints(job.query['filters'])

        filtered_sources = []
        if filter_constraints.get('sources'):
            filtered_sources = dash.views.helpers.get_filtered_sources(job.user, ','.join(filter_constraints.get('sources', [])))

        today = utils.dates_helper.local_today()
        expiry_date = today + datetime.timedelta(days=3)

        view, breakdowns = cls._extract_view_breakdown(job)
        ad_group_name, campaign_name, account_name = cls._extract_entity_names(job.user, filter_constraints)

        if job.scheduled_report:
            utils.email_helper.send_async_scheduled_report(
                job.user, job.query['options']['recipients'],
                job.scheduled_report.name,
                dash.constants.ScheduledReportSendingFrequency.get_text(
                    job.scheduled_report.sending_frequency),
                report_path, expiry_date,
                filter_constraints['start_date'], filter_constraints['end_date'],
                filtered_sources,
                job.query['options']['show_archived'], job.query['options']['show_blacklisted_publishers'],
                job.query['options']['include_totals'],
                view, breakdowns,
                cls._extract_column_names(job.query['fields']),
                ad_group_name, campaign_name, account_name,
            )
        else:
            utils.email_helper.send_async_report(
                job.user, job.query['options']['recipients'], report_path,
                filter_constraints['start_date'], filter_constraints['end_date'], expiry_date, filtered_sources,
                job.query['options']['show_archived'], job.query['options']['show_blacklisted_publishers'],
                view,
                breakdowns,
                cls._extract_column_names(job.query['fields']),
                job.query['options']['include_totals'],
                ad_group_name, campaign_name, account_name,
            )

    @staticmethod
    def _extract_view_breakdown(job):
        breakdowns = helpers.get_breakdown_names(job.query)
        if len(breakdowns) < 1:
            return '', []
        return breakdowns[0], ['By ' + breakdown for breakdown in breakdowns[1:]]

    @staticmethod
    def _extract_structure_constraints(constraints):
        structure_constraints = {}
        for field in constants.STRUCTURE_CONSTRAINTS_FIELDS:
            if field in constraints:
                structure_constraints[field + 's'] = [constraints[field]]
            elif field + '_list' in constraints:
                structure_constraints[field + 's'] = constraints[field + '_list']
        return structure_constraints

    @staticmethod
    def _extract_entity_names(user, constraints):
        if stats.constants.AD_GROUP in constraints:
            ad_group = dash.views.helpers.get_ad_group(user, constraints[stats.constants.AD_GROUP])
            return ad_group.name, ad_group.campaign.name, ad_group.campaign.account.name
        elif stats.constants.CAMPAIGN in constraints:
            campaign = dash.views.helpers.get_campaign(user, constraints[stats.constants.CAMPAIGN])
            return None, campaign.name, campaign.account.name
        elif stats.constants.ACCOUNT in constraints:
            account = dash.views.helpers.get_account(user, constraints[stats.constants.ACCOUNT])
            return None, None, account.name
        else:
            return None, None, None

    @staticmethod
    def _generate_random_filename():
        return ''.join(random.choice(string.letters + string.digits) for _ in range(64)) + '.csv'

    @staticmethod
    def _date_column_names(names):
        dated_columns = []
        original_to_dated_columns = {}
        for name in names:
            dated_name = name
            if utils.columns.FieldNames.from_column_name(name, raise_exception=False) in constants.DATED_COLUMNS:
                dated_name = utils.columns.add_date_to_name(name)
            dated_columns.append(dated_name)
            original_to_dated_columns[name] = dated_name
        return dated_columns, original_to_dated_columns

    @staticmethod
    def _get_order(job, field_name_mapping):
        order_fieldname = job.query['options'].get('order')
        if not order_fieldname:
            return constants.DEFAULT_ORDER

        prefix, fieldname = utils.sort_helper.dissect_order(order_fieldname)
        if fieldname not in field_name_mapping:
            return constants.DEFAULT_ORDER

        return prefix + fieldname
