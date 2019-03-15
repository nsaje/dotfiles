import datetime

from django.conf import settings
from influxdb import InfluxDBClient

import analytics.monitor
import utils.command_helpers
import utils.dates_helper
import utils.slack

INFLUX_MEASUREMENT = "z1_analytics_overspend"
ALERT_MSG_OVERSPEND = """Overspend on {date} on accounts:
{details}"""

OUTBRAIN_MSN_ACCOUNT = 3277
SKIP_ACCOUNTS = [OUTBRAIN_MSN_ACCOUNT]


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit autopilot job for today"

    def add_arguments(self, parser):
        parser.add_argument("--influx", dest="influx", action="store_true", help="Post metrics to influx")
        parser.add_argument("--date", "-d", dest="date", default=None, help="Date checked (default yesterday)")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        self.slack = options["slack"]
        self.date = utils.dates_helper.local_yesterday()
        if options["date"]:
            self.date = datetime.datetime.strptime(options["date"], "%Y-%m-%d")
        self.influx = options["influx"]
        self.influx_client = InfluxDBClient(**settings.INFLUX_DATABASES["default"])

        self._audit_overspend()

    def _audit_overspend(self):
        alarms = analytics.monitor.audit_overspend(self.date)
        if not alarms:
            return

        self._print(ALERT_MSG_OVERSPEND.format(date=self.date.strftime("%Y-%m-%d"), details=""))
        details = ""
        influx_data = []
        for account, account_overspend in list(alarms.items()):
            if account.id in SKIP_ACCOUNTS:
                continue
            self._print("- {} {}: ${:.2f}".format(account.name, account.id, account_overspend))
            details += " - {}: ${:.2f}\n".format(utils.slack.account_url(account), account_overspend)
            influx_data.append(
                {
                    "fields": {"overspend": float(account_overspend)},
                    "measurement": INFLUX_MEASUREMENT,
                    "tags": {"account_id": account.id},
                    "time": self.date.strftime("%Y-%m-%d") + "T12:00:00Z",
                }
            )
        if self.slack and details:
            utils.slack.publish(
                ALERT_MSG_OVERSPEND.format(date=self.date.strftime("%Y-%m-%d"), details=details),
                msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                username=utils.slack.USER_OVERSPEND,
            )
        if influx_data and self.influx:
            self.influx_client.write_points(influx_data)

    def _print(self, msg):
        if self.verbose:
            self.stdout.write("{}\n".format(msg))
