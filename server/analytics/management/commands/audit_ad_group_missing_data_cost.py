import analytics.monitor
import utils.command_helpers
import utils.slack
from utils import zlogging

logger = zlogging.getLogger(__name__)


MESSAGE = "Adgroup #{id} is missing some data cost"


class Command(utils.command_helpers.Z1Command):
    help = "Audit credits"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Post on Slack")
        parser.add_argument("--date", "-d", dest="date", default=None, help="Date checked (default today)")
        parser.add_argument("--days", "-n", dest="days", type=int, default=1, help="Days in the past to check")

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        self.date = options["date"]
        self.days = options["days"]
        self.slack = options["slack"]
        alarms = analytics.monitor.audit_ad_group_missing_data_cost(date=self.date, days=self.days)

        if not alarms:
            return

        text = "\n".join([MESSAGE.format(id=alarm) for alarm in alarms])

        if self.slack:
            try:
                utils.slack.publish(text, username=utils.slack.USER_AD_GROUP, channel=utils.slack.ALERTS_RND_PRODOPS)
            except Exception:
                logger.exception("Connection Error with Slack")

        self._print(text)
