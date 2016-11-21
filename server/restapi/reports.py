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

import utils.s3helpers
import utils.email_helper
import utils.columns


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
}


def get_breakdown_from_fields(fields):
    if not fields:
        raise serializers.ValidationError("Must define fields!")

    # take the first one
    return (fields[0]['field'],)


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
    return filter_constraints


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
            raw_report, goals = self.get_raw_report(self.job)
            csv_report = self.convert_to_csv(self.job, raw_report, goals)
            report_path = self.save_to_s3(csv_report)
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
        return rows, goals

    @classmethod
    def convert_to_csv(cls, job, data, goals):
        fieldnames = cls._extract_fieldnames(job.query['fields'])
        mapping = utils.columns.get_column_names_mapping(goals.pixels, goals.conversion_goals)

        output = StringIO.StringIO()
        writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
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
                row['publisher'] = row['breakdown_name']

    @staticmethod
    def _extract_fieldnames(fields_list):
        return [field_item['field'] for field_item in fields_list]

    @classmethod
    def save_to_s3(cls, csv):
        filename = cls._generate_random_filename()
        utils.s3helpers.S3Helper(settings.RESTAPI_REPORTS_BUCKET).put(filename, csv)
        return os.path.join(settings.RESTAPI_REPORTS_URL, filename)

    @classmethod
    def send_by_email(cls, job, report_path):
        if not job.query.get('options', {}).get('email_report'):
            return

        utils.email_helper.send_async_report(job.user, report_path)

    @staticmethod
    def _generate_random_filename():
        return ''.join(random.choice(string.letters + string.digits) for _ in range(64)) + '.csv'
