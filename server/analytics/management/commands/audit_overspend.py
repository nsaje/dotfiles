import datetime

from influxdb import InfluxDBClient
from django.conf import settings

import analytics.monitor
import utils.command_helpers
import utils.dates_helper
import utils.slack


INFLUX_MEASUREMENT = 'z1_analytics_overspend'
ALERT_MSG_OVERSPEND = u"""Overspend on {date} on accounts:
{details}"""


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit autopilot job for today"

    def add_arguments(self, parser):
        parser.add_argument('--influx', dest='influx', action='store_true',
                            help='Post metrics to influx')
        parser.add_argument('--date', '-d', dest='date', default=None,
                            help='Date checked (default yesterday)')
        parser.add_argument('--slack', dest='slack', action='store_true',
                            help='Notify via slack')
        parser.add_argument('--verbose', dest='verbose', action='store_true',
                            help='Display output')

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.slack = options['slack']
        self.date = utils.dates_helper.local_yesterday()
        if options['date']:
            self.date = datetime.datetime.strptime(options['date'], "%Y-%m-%d")
        self.influx = options['influx']
        self.influx_client = InfluxDBClient(**settings.INFLUX_DATABASES['default'])

        self._audit_overspend()

    def _audit_overspend(self):
        alarms = analytics.monitor.audit_overspend(self.date)
        if not alarms:
            return

        self._print(ALERT_MSG_OVERSPEND.format(date=self.date.strftime('%Y-%m-%d'), details=''))
        details = u''
        influx_data = []
        for account, account_overspend in alarms.items():
            self._print(u'- {} {}: ${:.2f}'.format(account.name, account.id, account_overspend))
            details += u' - {}: ${:.2f}\n'.format(
                utils.slack.account_url(account),
                account_overspend,
            )
            influx_data.append({
                'fields': {'overspend': float(account_overspend)},
                'measurement': INFLUX_MEASUREMENT,
                'tags': {'account_id': account.id},
                'time': self.date.strftime('%Y-%m-%d') + 'T12:00:00Z',
            })
        if self.slack:
            utils.slack.publish(
                ALERT_MSG_OVERSPEND.format(date=self.date.strftime('%Y-%m-%d'), details=details),
                msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                username='Overspend monitoring',
            )
        if influx_data and self.influx:
            self.influx_client.write_points(influx_data)
