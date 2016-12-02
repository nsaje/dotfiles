import abc
import datetime
import logging
import random
import string
import unicodecsv
import StringIO
import os.path

from django.conf import settings
from rest_framework import serializers

from dash import constants
from dash.views import helpers
import dash.models

import stats.constants
import stats.api_breakdowns
import stats.api_reports

import utils.s3helpers
import utils.email_helper
import utils.columns
import utils.sort_helper
import utils.dates_helper


logger = logging.getLogger(__name__)

MAX_ROWS = 999999

EQUALS = '='
IN = 'IN'
BETWEEN = 'between'
OPERATORS = [EQUALS, IN, BETWEEN]

SUPPORTED_BREAKDOWNS = {
    (utils.columns.Names.content_ad_id,),
    (utils.columns.Names.source_id,),
    (utils.columns.Names.publisher,),
    (utils.columns.Names.publisher, utils.columns.Names.day),
    (utils.columns.Names.publisher, utils.columns.Names.week),
    (utils.columns.Names.publisher, utils.columns.Names.month),
}

DATED_COLUMNS = (
    utils.columns.Names.status,
)


def get_breakdown_from_fields(fields):
    if not fields:
        raise serializers.ValidationError("Must define fields!")

    breakdown = [fields[0]['field']]
    if len(fields) > 1 and fields[1]['field'] in (
            utils.columns.Names.day, utils.columns.Names.week, utils.columns.Names.month):
        breakdown.append(fields[1]['field'])

    return tuple(breakdown)


def get_filter_constraints(filters):
    filter_constraints = {}
    for f in filters:
        if f['field'] == utils.columns.Names.ad_group_id and f['operator'] == EQUALS:
            filter_constraints['ad_group_id'] = int(f['value'])
        if f['field'] == utils.columns.Names.date and f['operator'] == BETWEEN:
            filter_constraints['start_date'] = _parse_date(f['from'])
            filter_constraints['end_date'] = _parse_date(f['to'])
        if f['field'] == utils.columns.Names.date and f['operator'] == EQUALS:
            date = _parse_date(f['value'])
            filter_constraints['start_date'] = date
            filter_constraints['end_date'] = date
        if f['field'] == utils.columns.Names.source and f['operator'] == EQUALS:
            filter_constraints['sources'] = [f['value']]
        if f['field'] == utils.columns.Names.source and f['operator'] == IN:
            filter_constraints['sources'] = f['values']
    return filter_constraints


def get_options(options):
    return {
        'show_archived': options.get('show_archived') or False,
        'email_report': options.get('email_report') or False,
        'show_blacklisted_publishers': (options.get('show_blacklisted_publishers') or
                                        constants.PublisherBlacklistFilter.SHOW_ALL),
        'include_totals': options.get('include_totals') or False,
        'show_status_date': options.get('show_status_date') or False,
        'recipients': options.get('recipients') or [],
    }


def _parse_date(string):
    try:
        return datetime.datetime.strptime(string, '%Y-%m-%d').date()
    except ValueError:
        raise serializers.ValidationError("Invalid date format")


class ReportNamesSerializer(serializers.Serializer):
    field = serializers.CharField(allow_blank=False, trim_whitespace=True)


class ReportFiltersSerializer(serializers.Serializer):
    field = serializers.CharField(allow_blank=False, trim_whitespace=True)
    operator = serializers.ChoiceField(OPERATORS)
    value = serializers.CharField(required=False)
    values = serializers.ListField(child=serializers.CharField(), required=False)
    frm = serializers.CharField(required=False)  # remapped to 'from' below
    to = serializers.CharField(required=False)
# from is a reserved keyword, remap it directly
ReportFiltersSerializer._declared_fields['from'] = ReportFiltersSerializer._declared_fields['frm']
del ReportFiltersSerializer._declared_fields['frm']


class ReportOptionsSerializer(serializers.Serializer):
    email_report = serializers.BooleanField(default=False)
    show_archived = serializers.BooleanField(default=False)
    show_blacklisted_publishers = serializers.ChoiceField(
        constants.PublisherBlacklistFilter.get_all(), required=False)
    include_totals = serializers.BooleanField(default=False)
    show_status_date = serializers.BooleanField(default=False)
    recipients = serializers.ListField(child=serializers.EmailField(), required=False)


class ReportQuerySerializer(serializers.Serializer):
    fields = ReportNamesSerializer(many=True)
    filters = ReportFiltersSerializer(many=True)
    options = ReportOptionsSerializer(required=False)

    def validate_fields(self, fields):
        breakdown = get_breakdown_from_fields(fields)
        if breakdown not in SUPPORTED_BREAKDOWNS:
            raise serializers.ValidationError("Breakdown %s not supported!" % str(breakdown))
        return fields

    def validate_filters(self, filters):
        filter_constraints = get_filter_constraints(filters)
        if 'ad_group_id' not in filter_constraints:
            raise serializers.ValidationError("Please specify a single ad group in filters!")
        if 'start_date' not in filter_constraints or 'end_date' not in filter_constraints:
            raise serializers.ValidationError("Please specify a date range!")
        return filters


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

    def execute(self):
        if self.job.status != constants.ReportJobStatus.IN_PROGRESS:
            logger.warning('Running a job executor on a job in incorrect state: %s' % self.job.status)
            return

        try:
            # temporary switch while new reports are developed
            if self.job.query['fields'][0]['field'] == 'Publisher':
                raw_report, goals, filename = self.get_raw_new_report(self.job)
            else:
                raw_report, goals, filename = self.get_raw_report(self.job)
            csv_report = self.convert_to_csv(self.job, raw_report, goals)
            report_path = self.save_to_s3(csv_report, filename)
            self.send_by_email(self.job, report_path)

            self.job.result = report_path
            self.job.status = constants.ReportJobStatus.DONE
        except Exception as e:
            self.job.status = constants.ReportJobStatus.FAILED
            self.job.result = str(e)
            logger.exception('Exception when processing API report job %s' % self.job.id)
        finally:
            self.job.save()

    @classmethod
    def get_raw_new_report(cls, job):
        breakdown = list(get_breakdown_from_fields(job.query['fields']))
        breakdown = utils.columns.Names.get_keys(breakdown)
        breakdown = [stats.constants.get_dimension_identifier(x) for x in breakdown]

        user = job.user

        filter_constraints = get_filter_constraints(job.query['filters'])
        ad_group_id = filter_constraints['ad_group_id']
        start_date = filter_constraints['start_date']
        end_date = filter_constraints['end_date']
        filtered_sources = helpers.get_filtered_sources(user, ','.join(filter_constraints.get('sources', [])))

        options = get_options(job.query.get('options', {}))

        ad_group = helpers.get_ad_group(user, ad_group_id)
        constraints = stats.api_reports.prepare_constraints(
            user, breakdown, start_date, end_date, filtered_sources,
            show_archived=options['show_archived'],
            show_blacklisted_publishers=options['show_blacklisted_publishers'],
            ad_group_ids=[ad_group.id])
        goals = stats.api_reports.get_goals(constraints)

        rows = stats.api_reports.query(user, breakdown, constraints, goals, '-clicks')

        cls.remap_columns(rows, breakdown)

        rows = utils.sort_helper.sort_results(rows, breakdown)

        if options['include_totals']:
            totals = stats.api_reports.totals(user, breakdown, constraints, goals)
            rows.append(totals)

        return rows, goals, stats.api_reports.get_filename(breakdown, constraints)

    @classmethod
    def get_raw_report(cls, job):
        breakdown = list(get_breakdown_from_fields(job.query['fields']))
        breakdown = utils.columns.Names.get_keys(breakdown)
        breakdown = [stats.constants.get_dimension_identifier(x) for x in breakdown]

        filter_constraints = get_filter_constraints(job.query['filters'])
        ad_group_id = filter_constraints['ad_group_id']
        start_date = filter_constraints['start_date']
        end_date = filter_constraints['end_date']

        level = constants.Level.AD_GROUPS
        user = job.user
        stats.api_breakdowns.validate_breakdown_allowed(level, user, breakdown)
        ad_group = helpers.get_ad_group(user, ad_group_id)
        target_dim = stats.constants.get_target_dimension(breakdown)
        filtered_sources = dash.models.Source.objects.all()
        constraints = stats.constraints_helper.prepare_ad_group_constraints(
            user, ad_group, breakdown,
            only_used_sources=target_dim == 'source_id',
            start_date=start_date, end_date=end_date, filtered_sources=filtered_sources)
        goals = stats.api_breakdowns.get_goals(constraints)
        parents = []
        offset = 0
        limit = MAX_ROWS

        rows = stats.api_breakdowns.query(
            level,
            user,
            breakdown,
            constraints,
            goals,
            parents,
            '-clicks',
            offset,
            limit,
        )

        cls.remap_columns(rows, breakdown)
        return rows, goals, None

    @classmethod
    def convert_to_csv(cls, job, data, goals):
        options = get_options(job.query.get('options', {}))

        fieldnames = cls._extract_fieldnames(job.query['fields'])
        mapping = utils.columns.get_column_names_mapping(goals.pixels, goals.conversion_goals)

        if options['show_status_date']:
            fieldnames = cls._date_fieldnames(fieldnames)
            mapping = cls._date_field_name_mapping(mapping)

        output = StringIO.StringIO()
        writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel',
                                       quoting=unicodecsv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            csv_row = {}
            for column, value in row.items():
                if column in mapping and mapping[column] in fieldnames:
                    csv_row[mapping[column]] = value
            writer.writerow(csv_row)
        return output.getvalue()

    @classmethod
    def remap_columns(cls, rows, breakdown):
        # temporary fix for naming discrepancies between reports and breakdowns
        for row in rows:
            if 'exchange' in row:
                row['source'] = row['exchange']
            if breakdown == ['source_id']:
                row['source'] = row['breakdown_name']
            if breakdown == ['content_ad_id']:
                row['content_ad'] = row['breakdown_name']
            if breakdown == ['publisher_id']:
                row['publisher'] = row.get('breakdown_name', row['domain'])

    @staticmethod
    def _extract_fieldnames(fields_list):
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
        utils.s3helpers.S3Helper(settings.RESTAPI_REPORTS_BUCKET).put(filename, csv, human_readable_filename)
        return os.path.join(settings.RESTAPI_REPORTS_URL, filename)

    @classmethod
    def send_by_email(cls, job, report_path):
        if not job.query.get('options', {}).get('email_report'):
            return

        filter_constraints = get_filter_constraints(job.query['filters'])

        filtered_sources = []
        if filter_constraints.get('sources'):
            filtered_sources = helpers.get_filtered_sources(job.user, ','.join(filter_constraints.get('sources', [])))

        options = get_options(job.query.get('options', {}))

        today = utils.dates_helper.local_today()
        expiry_date = today + datetime.timedelta(days=3)

        utils.email_helper.send_async_report(
            job.user, options['recipients'], report_path,
            filter_constraints['start_date'], filter_constraints['end_date'], expiry_date, filtered_sources,
            options['show_archived'], options['show_blacklisted_publishers'],
            get_breakdown_from_fields(job.query['fields']),
            cls._extract_fieldnames(job.query['fields']),
            options['include_totals'],
            ad_group=helpers.get_ad_group(job.user, filter_constraints['ad_group_id'])
        )

    @staticmethod
    def _generate_random_filename():
        return ''.join(random.choice(string.letters + string.digits) for _ in range(64)) + '.csv'

    @staticmethod
    def _date_field_name_mapping(mapping):
        return {k: (utils.columns.add_date_to_name(v) if v in DATED_COLUMNS else v) for k, v in mapping.items()}

    @staticmethod
    def _date_fieldnames(fieldnames):
        return [(utils.columns.add_date_to_name(x) if x in DATED_COLUMNS else x) for x in fieldnames]
