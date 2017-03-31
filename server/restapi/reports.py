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

from restapi import models

from server import celery

import stats.constants
import stats.api_breakdowns
import stats.api_reports

import utils.s3helpers
import utils.email_helper
import utils.columns
import utils.sort_helper
import utils.dates_helper
from utils import exc


logger = logging.getLogger(__name__)

MAX_ROWS = 999999

EQUALS = '='
IN = 'IN'
BETWEEN = 'between'
OPERATORS = [EQUALS, IN, BETWEEN]

DEFAULT_ORDER = '-e_media_cost'

DATED_COLUMNS = (
    utils.columns.FieldNames.status,
    utils.columns.FieldNames.account_status,
    utils.columns.FieldNames.campaign_status,
    utils.columns.FieldNames.ad_group_status,
    utils.columns.FieldNames.content_ad_status,
    utils.columns.FieldNames.source_status,
    utils.columns.FieldNames.publisher_status,
)

BREAKDOWN_FIELDS = set(
    stats.constants.StructureDimension._ALL +
    stats.constants.TimeDimension._ALL +
    stats.constants.DeliveryDimension._ALL)

STRUCTURE_CONSTRAINTS_FIELDS = ['account_id', 'campaign_id', 'ad_group_id', 'content_ad_id']


def get_breakdown_from_fields(fields):
    if not fields:
        raise serializers.ValidationError("Must define fields!")

    def _dimension_identifier(field):
        return stats.constants.get_dimension_identifier(utils.columns.FieldNames.from_column_name(field, raise_exception=False))

    dimension_identifiers = [_dimension_identifier(field['field']) for field in fields]

    breakdown = []
    for di in dimension_identifiers:
        if di in BREAKDOWN_FIELDS and di not in breakdown:
            breakdown.append(di)

    if utils.columns.FieldNames.publisher_id in breakdown and utils.columns.FieldNames.source_id in breakdown:
        breakdown.remove(utils.columns.FieldNames.source_id)

    return breakdown


def get_filter_constraints(filters):
    filter_constraints = {}
    for f in filters:
        field_name = utils.columns.FieldNames.from_column_name(f['field'])

        if field_name in STRUCTURE_CONSTRAINTS_FIELDS:
            if f['operator'] == EQUALS:
                filter_constraints[field_name] = int(f['value'])
            elif f['operator'] == IN:
                filter_constraints[field_name + '_list'] = [int(v) for v in f['values']]
        if field_name == utils.columns.FieldNames.date and f['operator'] == BETWEEN:
            filter_constraints['start_date'] = _parse_date(f['from'])
            filter_constraints['end_date'] = _parse_date(f['to'])
        if field_name == utils.columns.FieldNames.date and f['operator'] == EQUALS:
            date = _parse_date(f['value'])
            filter_constraints['start_date'] = date
            filter_constraints['end_date'] = date
        if field_name == utils.columns.FieldNames.source and f['operator'] == EQUALS:
            filter_constraints['sources'] = [f['value']]
        if field_name == utils.columns.FieldNames.source and f['operator'] == IN:
            filter_constraints['sources'] = f['values']
        if field_name == utils.columns.FieldNames.agency and f['operator'] == IN:
            filter_constraints['agencies'] = f['values']
        if field_name == utils.columns.FieldNames.account_type and f['operator'] == IN:
            filter_constraints['account_types'] = f['values']
    return filter_constraints


def get_level_from_constraints(constraints):
    if stats.constants.AD_GROUP in constraints:
        return dash.constants.Level.AD_GROUPS
    elif 'content_ad_id_list' in constraints:
        return dash.constants.Level.AD_GROUPS
    elif stats.constants.CAMPAIGN in constraints:
        return dash.constants.Level.CAMPAIGNS
    elif 'ad_group_id_list' in constraints:
        return dash.constants.Level.CAMPAIGNS
    elif stats.constants.ACCOUNT in constraints:
        return dash.constants.Level.ACCOUNTS
    elif 'campaign_id_list' in constraints:
        return dash.constants.Level.ACCOUNTS
    else:
        return dash.constants.Level.ALL_ACCOUNTS


def limit_breakdown_to_level(breakdown, level):
    if level == dash.constants.Level.AD_GROUPS:
        constraint_dimension = stats.constants.AD_GROUP
    elif level == dash.constants.Level.CAMPAIGNS:
        constraint_dimension = stats.constants.CAMPAIGN
    elif level == dash.constants.Level.ACCOUNTS:
        constraint_dimension = stats.constants.ACCOUNT
    else:
        return breakdown
    return stats.constants.get_child_breakdown_of_dimension(breakdown, constraint_dimension)


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
        constants.PublisherBlacklistFilter.get_all(), default=constants.PublisherBlacklistFilter.SHOW_ALL)
    include_totals = serializers.BooleanField(default=False)
    include_items_with_no_spend = serializers.BooleanField(default=False)
    show_status_date = serializers.BooleanField(default=False)
    recipients = serializers.ListField(child=serializers.EmailField(), default=[])
    order = serializers.CharField(required=False)


class ReportQuerySerializer(serializers.Serializer):
    fields = ReportNamesSerializer(many=True)
    filters = ReportFiltersSerializer(many=True)
    options = ReportOptionsSerializer(default={})

    def validate_filters(self, filters):
        filter_constraints = get_filter_constraints(filters)
        if 'start_date' not in filter_constraints or 'end_date' not in filter_constraints:
            raise serializers.ValidationError("Please specify a date range!")
        if 'ad_group_id' in filter_constraints:
            helpers.get_ad_group(self.context['request'].user, filter_constraints['ad_group_id'])
        if 'campaign_id' in filter_constraints:
            helpers.get_campaign(self.context['request'].user, filter_constraints['campaign_id'])
        if 'account_id' in filter_constraints:
            helpers.get_account(self.context['request'].user, filter_constraints['account_id'])
        return filters

    def validate(self, data):
        filter_constraints = get_filter_constraints(data['filters'])
        level = get_level_from_constraints(filter_constraints)
        breakdown = get_breakdown_from_fields(data['fields'])
        try:
            stats.api_reports.validate_breakdown_by_structure(level, breakdown)
            stats.api_reports.validate_breakdown_by_permissions(level, self.context['request'].user, breakdown)
        except exc.InvalidBreakdownError as e:
            raise serializers.ValidationError(e)
        if stats.constants.get_delivery_dimension(breakdown):
            raise serializers.ValidationError("Delivery dimension not supported!")
        return data


@celery.app.task(acks_late=True, name='reports_execute')
def execute(job_id):
    job = models.ReportJob.objects.get(pk=job_id)
    executor = ReportJobExecutor(job)
    executor.execute()


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
            raw_report, field_name_mapping, filename = self.get_raw_new_report(self.job)

            csv_report = self.convert_to_csv(self.job, raw_report, field_name_mapping)
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
        user = job.user

        breakdown = list(get_breakdown_from_fields(job.query['fields']))
        filter_constraints = get_filter_constraints(job.query['filters'])
        start_date = filter_constraints['start_date']
        end_date = filter_constraints['end_date']
        filtered_sources = helpers.get_filtered_sources(user, ','.join(filter_constraints.get('sources', [])))
        filtered_account_types = helpers.get_filtered_account_types(filter_constraints.get('account_types', []))
        filtered_agencies = helpers.get_filtered_agencies(filter_constraints.get('agencies', []))

        level = get_level_from_constraints(filter_constraints)
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
        goals = stats.api_reports.get_goals(constraints)

        field_name_mapping = utils.columns.get_field_names_mapping(
            goals.pixels, goals.conversion_goals,
            show_publishers_fields=stats.constants.PUBLISHER in breakdown
        )

        order = cls._get_order(job, field_name_mapping)

        rows = stats.api_reports.query(
            user, breakdown, constraints, goals, order, level,
            include_items_with_no_spend=job.query['options']['include_items_with_no_spend'])

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
                user, limit_breakdown_to_level(breakdown, level),
                totals_constraints, goals, level)
            rows.append(totals)

        return rows, field_name_mapping, stats.api_reports.get_filename(breakdown, constraints)

    @classmethod
    def convert_to_csv(cls, job, data, field_name_mapping):
        requested_columns = cls._extract_column_names(job.query['fields'])

        csv_column_names = requested_columns
        original_to_dated = {k: k for k in requested_columns}
        if job.query['options']['show_status_date']:
            csv_column_names, original_to_dated = cls._date_column_names(csv_column_names)

        output = StringIO.StringIO()
        writer = unicodecsv.DictWriter(output, csv_column_names, encoding='utf-8', dialect='excel',
                                       quoting=unicodecsv.QUOTE_ALL)
        writer.writeheader()
        for row in data:
            csv_row = {}
            for column_name in requested_columns:
                field_name = field_name_mapping[column_name]
                csv_column = original_to_dated[column_name]
                if field_name in row:
                    csv_row[csv_column] = row[field_name]
                else:
                    csv_row[csv_column] = dash.export._format_empty_value(None, field_name)
            writer.writerow(csv_row)
        return output.getvalue()

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
        utils.s3helpers.S3Helper(settings.RESTAPI_REPORTS_BUCKET).put(filename, csv, human_readable_filename)
        return os.path.join(settings.RESTAPI_REPORTS_URL, filename)

    @classmethod
    def send_by_email(cls, job, report_path):
        if not job.query['options']['email_report']:
            return

        filter_constraints = get_filter_constraints(job.query['filters'])

        filtered_sources = []
        if filter_constraints.get('sources'):
            filtered_sources = helpers.get_filtered_sources(job.user, ','.join(filter_constraints.get('sources', [])))

        today = utils.dates_helper.local_today()
        expiry_date = today + datetime.timedelta(days=3)

        view, breakdowns = cls._extract_view_breakdown(job)
        ad_group_name, campaign_name, account_name = cls._extract_entity_names(job.user, filter_constraints)
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
        breakdowns = limit_breakdown_to_level(
            get_breakdown_from_fields(job.query['fields']),
            get_level_from_constraints(get_filter_constraints(job.query['filters'])),
        )

        breakdowns = [breakdown[:-3] if breakdown.endswith('_id') else breakdown for breakdown in breakdowns]
        breakdowns = [utils.columns._FIELD_MAPPING[breakdown][0] for breakdown in breakdowns]
        if len(breakdowns) < 1:
            return '', []
        return breakdowns[0], ['By ' + breakdown for breakdown in breakdowns[1:]]

    @staticmethod
    def _extract_structure_constraints(constraints):
        structure_constraints = {}
        for field in STRUCTURE_CONSTRAINTS_FIELDS:
            if field in constraints:
                structure_constraints[field + 's'] = [constraints[field]]
            elif field + '_list' in constraints:
                structure_constraints[field + 's'] = constraints[field + '_list']
        return structure_constraints

    @staticmethod
    def _extract_entity_names(user, constraints):
        if stats.constants.AD_GROUP in constraints:
            ad_group = helpers.get_ad_group(user, constraints[stats.constants.AD_GROUP])
            return ad_group.name, ad_group.campaign.name, ad_group.campaign.account.name
        elif stats.constants.CAMPAIGN in constraints:
            campaign = helpers.get_campaign(user, constraints[stats.constants.CAMPAIGN])
            return None, campaign.name, campaign.account.name
        elif stats.constants.ACCOUNT in constraints:
            account = helpers.get_account(user, constraints[stats.constants.ACCOUNT])
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
            if utils.columns.FieldNames.from_column_name(name, raise_exception=False) in DATED_COLUMNS:
                dated_name = utils.columns.add_date_to_name(name)
            dated_columns.append(dated_name)
            original_to_dated_columns[name] = dated_name
        return dated_columns, original_to_dated_columns

    @staticmethod
    def _get_order(job, field_name_mapping):
        order_fieldname = job.query['options'].get('order')
        if not order_fieldname:
            return DEFAULT_ORDER

        prefix, fieldname = utils.sort_helper.dissect_order(order_fieldname)

        try:
            field_key = field_name_mapping[fieldname]
        except:
            # the above will fail when we are sorting by name as we are remapping those columns
            # to the dimension name
            field_key = 'name'

        return prefix + field_key
