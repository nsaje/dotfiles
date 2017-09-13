from collections import defaultdict
import datetime
import logging

from influxdb import InfluxDBClient
from django.conf import settings

import stats.api_breakdowns
import redshiftapi.api_breakdowns
from stats.helpers import Goals
from utils.command_helpers import ExceptionCommand, parse_date
from dash import constants
from dash import models
from core.publisher_groups import publisher_group_helpers
import zemauth.models

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def add_arguments(self, parser):
        parser.add_argument('--from', help='Date from iso format')
        parser.add_argument('--to', help='Date to iso format')

    def handle(self, *args, **options):
        today = datetime.date.today()
        date_from = parse_date(options, 'from') or today - datetime.timedelta(days=3)
        date_to = parse_date(options, 'to') or today

        influx = InfluxDBClient(**settings.INFLUX_DATABASES['default'])

        date = date_from
        while date <= date_to:
            self._redshift_to_influx(influx, date, ['ad_group_id', 'campaign_id', 'account_id', 'source_id'], 'adgroupdata')

            self._stats_to_influx(influx, date, 'account_id', 'account_mtd')

            self._stats_to_influx(influx, date, 'source_id', 'source_mtd')

            self._stats_to_influx(influx, date, 'publisher_id', 'publisher_mtd')

            self._agency_to_influx(influx, date, 'agency_mtd')

            date += datetime.timedelta(days=1)

    def _agency_to_influx(self, influx, date, measurement):
        data = redshiftapi.api_breakdowns.query(
            ['account_id'],
            {
                'date__lte': date,
                'date__gte': datetime.date(date.year, date.month, 1),
            },
            None,
            Goals([], [], [], [], []),
            '-total_cost',
            0,
            10000,
        )
        accounts = {account.id: account for account in models.Account.objects.select_related('agency').filter(agency__isnull=False)}

        data_by_agency = defaultdict(lambda: {'clicks': 0.0, 'billing_cost': 0.0, 'impressions': 0.0})
        for entry in data:
            account = accounts.get(entry['account_id'])
            if account is None:
                continue
            agency = account.agency
            data_by_agency[agency.id]['name'] = agency.name
            data_by_agency[agency.id]['agency_id'] = agency.id
            data_by_agency[agency.id]['clicks'] += float(entry['clicks'] if entry['clicks'] else 0)
            data_by_agency[agency.id]['impressions'] += float(entry['impressions'] if entry['impressions'] else 0)
            data_by_agency[agency.id]['billing_cost'] += float(entry['billing_cost'] if entry['billing_cost'] else 0)

        tags = set(['agency_id', 'name'])
        fields = set(['clicks', 'billing_cost', 'impressions'])

        influx_data = [{
            'fields': {field: float(entry.get(field) or 0) for field in fields},
            'measurement': measurement,
            'tags': {key: value for key, value in entry.iteritems() if key in tags},
            'time': date.strftime('%Y-%m-%d') + 'T12:00:00Z'
        } for entry in data_by_agency.itervalues()]

        influx.write_points(influx_data)

    def _redshift_to_influx(self, influx, date, breakdown, measurement):
        data = redshiftapi.api_breakdowns.query(
            breakdown,
            {
                'date': date,
            },
            None,
            Goals([], [], [], [], []),
            '-total_cost',
            0,
            10000,
        )

        tags = set(breakdown)

        influx_data = [{
            'fields': {key: float(value) for key, value in entry.iteritems() if key not in tags and value is not None},
            'measurement': measurement,
            'tags': {key: value for key, value in entry.iteritems() if key in tags},
            'time': date.strftime('%Y-%m-%d') + 'T12:00:00Z'
        } for entry in data]

        influx.write_points(influx_data)

    def _stats_to_influx(self, influx, date, breakdown, measurement):
        data = stats.api_breakdowns.query(
            constants.Level.ALL_ACCOUNTS,
            zemauth.models.User.objects.get(pk=423),
            [breakdown],
            {
                'date__lte': date,
                'date__gte': datetime.date(date.year, date.month, 1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'publisher_blacklist_filter': constants.PublisherBlacklistFilter.SHOW_ALL,
                'publisher_blacklist': models.PublisherGroupEntry.objects.none(),
                'publisher_whitelist': models.PublisherGroupEntry.objects.none(),
                'publisher_group_targeting': publisher_group_helpers.get_default_publisher_group_targeting_dict(),
            },
            Goals([], [], [], [], []),
            None,
            '-total_cost',
            0,
            1000,
        )

        tags = set([breakdown, 'name'])
        fields = set(['clicks', 'billing_cost', 'impressions'])

        influx_data = [{
            'fields': {field: float(entry.get(field) or 0) for field in fields},
            'measurement': measurement,
            'tags': {key: value for key, value in entry.iteritems() if key in tags},
            'time': date.strftime('%Y-%m-%d') + 'T12:00:00Z'
        } for entry in data]

        influx.write_points(influx_data)
