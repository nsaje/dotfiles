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


logger = logging.getLogger(__name__)

MAX_ROWS = 999999

DATE = 'Date'
AD_GROUP_ID = 'Ad Group Id'
CONTENT_AD_ID = 'Content Ad Id'
CONTENT_AD_TITLE = 'Content Ad'
DOMAIN_ID = 'Domain Id'
DOMAIN = 'Domain'
MEDIA_SOURCE_NAME = 'Media Source'
MEDIA_SOURCE_ID = 'Media Source Id'
CONTENT_AD_LABEL = 'Label'
TOTAL_SPEND = 'Total Spend'
IMPRESSIONS = 'Impressions'
CLICKS = 'Clicks'
AVG_CPC = 'Avg. CPC'

FIELDS = {
    DATE: 'date',
    AD_GROUP_ID: 'ad_group_id',
    CONTENT_AD_ID: 'content_ad_id',
    CONTENT_AD_TITLE: 'title',
    CONTENT_AD_LABEL: 'label',
    DOMAIN_ID: 'publisher_id',
    DOMAIN: 'domain',
    MEDIA_SOURCE_NAME: 'name',
    MEDIA_SOURCE_ID: 'source_id',
    TOTAL_SPEND: 'billing_cost',
    IMPRESSIONS: 'impressions',
    CLICKS: 'clicks',
    AVG_CPC: 'cpc',
}

EQUALS = '='
IN = 'IN'
BETWEEN = 'between'
OPERATORS = [EQUALS, IN, BETWEEN]

SUPPORTED_BREAKDOWNS = {
    ('content_ad_id',),
    ('source_id',),
    ('publisher_id',),
}


def get_breakdown_from_fields(fields):
    if not fields:
        raise serializers.ValidationError("Must define fields!")
    breakdown = (FIELDS[fields[0]['field']],)
    return breakdown


def get_filter_constraints(filters):
    filter_constraints = {}
    for f in filters:
        if f['field'] == AD_GROUP_ID and f['operator'] == EQUALS:
            filter_constraints['ad_group_id'] = int(f['value'])
        if f['field'] == DATE and f['operator'] == BETWEEN:
            filter_constraints['start_date'] = _parse_date(f['from'])
            filter_constraints['end_date'] = _parse_date(f['to'])
        if f['field'] == DATE and f['operator'] == EQUALS:
            date = _parse_date(f['value'])
            filter_constraints['start_date'] = date
            filter_constraints['end_date'] = date
    return filter_constraints


def _parse_date(string):
    try:
        return datetime.datetime.strptime(string, '%Y-%m-%d').date()
    except ValueError:
        raise serializers.ValidationError("Invalid date format")


class ReportFieldsSerializer(serializers.Serializer):
    field = serializers.ChoiceField(FIELDS)


class ReportFiltersSerializer(serializers.Serializer):
    field = serializers.ChoiceField(FIELDS)
    operator = serializers.ChoiceField(OPERATORS)
    value = serializers.CharField(required=False)
    values = serializers.ListField(child=serializers.CharField(), required=False)
    frm = serializers.CharField(required=False)  # remapped to 'from' below
    to = serializers.CharField(required=False)
# from is a reserved keyword, remap it directly
ReportFiltersSerializer._declared_fields['from'] = ReportFiltersSerializer._declared_fields['frm']
del ReportFiltersSerializer._declared_fields['frm']


class ReportQuerySerializer(serializers.Serializer):
    fields = ReportFieldsSerializer(many=True)
    filters = ReportFiltersSerializer(many=True)

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
            raw_report = self.get_raw_report(self.job)
            csv_report = self.convert_to_csv(self.job, raw_report)
            report_path = self.save_to_s3(csv_report)
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
        return rows

    @classmethod
    def convert_to_csv(cls, job, data):
        fieldnames = cls._extract_fieldnames(job.query['fields'])
        output = StringIO.StringIO()
        writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            csv_row = {}
            for field in fieldnames:
                formatted_value = row.get(FIELDS[field])
                csv_row[field] = formatted_value
            writer.writerow(csv_row)
        return output.getvalue()

    @staticmethod
    def _extract_fieldnames(fields_list):
        return [field_item['field'] for field_item in fields_list]

    @classmethod
    def save_to_s3(cls, csv):
        filename = cls._generate_random_filename()
        utils.s3helpers.S3Helper(settings.RESTAPI_REPORTS_BUCKET).put(filename, csv)
        return os.path.join(settings.RESTAPI_REPORTS_URL, filename)

    @staticmethod
    def _generate_random_filename():
        return ''.join(random.choice(string.letters + string.digits) for _ in range(64)) + '.csv'
