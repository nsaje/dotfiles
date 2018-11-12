import analytics.monitor
import utils.command_helpers
import utils.slack

ALERT_MSG = """Yesterday, Ad group *{name}* (<https://one.zemanta.com/v2/analytics/adgroup/{ad_group_id}/sources | {ad_group_id}>)
spend ${total_spend} with too high eCPC (${ecpc}) compared to its bid CPC (${cpc}) on *{source_name}*.
"""


class Command(utils.command_helpers.ExceptionCommand):
    help = "Alert about the differences between CPC and ECPC an all ad group sources" "of all active ad groups"

    def add_arguments(self, parser):
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")

    def handle(self, *args, **options):
        self.slack = options["slack"]
        self._audit_cpc_vs_ecpc()

    def _print(self, *msg):
        self.stdout.write("{} \n".format(*msg))

    def _audit_cpc_vs_ecpc(self):
        alarms = analytics.monitor.audit_bid_cpc_vs_ecpc()
        if not alarms:
            return
        messages = [ALERT_MSG.format(**alarm) for alarm in alarms]
        text = "\n".join(messages)
        if not self.slack:
            self.stdout.write(text)
            return
        utils.slack.publish(
            text, msg_type=utils.slack.MESSAGE_TYPE_WARNING, username="Audit CPC", channel="z1-monitoring"
        )
