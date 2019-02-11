import analytics.monitor
import utils.command_helpers
import utils.slack

ALERT_MSG_AD_GROUPS = """Autopilot did not run today on the following ad groups:
{}"""
ALERT_MSG_CPC_CHANGES = """Autopilot made irregular CPC adjustments on the following sources:
{}"""
ALERT_MSG_BUDGET_CHANGES = """Autopilot made irregular budget adjustments on the following ad groups:
{}"""


class Command(utils.command_helpers.ExceptionCommand):
    help = "Audit autopilot job for today"

    def add_arguments(self, parser):
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        self.slack = options["slack"]

        self._audit_autopilot_ad_groups()
        self._audit_autopilot_daily_caps_changes()
        self._audit_autopilot_cpc_changes()

    def _audit_autopilot_ad_groups(self):
        alarms = analytics.monitor.audit_autopilot_ad_groups()
        if not alarms:
            return

        details = ""
        for ad_group in alarms:
            self._print("- {} {}".format(ad_group.name, ad_group.pk))
            details += " - {}\n".format(utils.slack.ad_group_url(ad_group))
        if self.slack:
            utils.slack.publish(
                ALERT_MSG_AD_GROUPS.format(details),
                msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                username=utils.slack.USER_AUTOPILOT,
            )
            return
        self._print(ALERT_MSG_AD_GROUPS.format(details))

    def _audit_autopilot_daily_caps_changes(self):
        alarms = analytics.monitor.audit_autopilot_daily_caps_changes()
        if not alarms:
            return
        details = ""
        for ad_group, error in alarms.items():
            self._print("- {} {}: {}".format(str(ad_group.name), ad_group.pk, error))
            details += " - {}: {}$\n".format(utils.slack.ad_group_url(ad_group), error)
        if self.slack:
            utils.slack.publish(
                ALERT_MSG_BUDGET_CHANGES.format(details),
                msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                username=utils.slack.USER_AUTOPILOT,
            )
            return
        self._print(ALERT_MSG_BUDGET_CHANGES.format(details))

    def _audit_autopilot_cpc_changes(self):
        alarms = analytics.monitor.audit_autopilot_cpc_changes()
        if not alarms:
            return
        details = ""
        for source, error in alarms.items():
            error_msg = "all adjustments were positive" if error > 0 else "all adjustments were negative"
            self._print("- {}: {}".format(source.name, error_msg))
            details += " - {}: {}\n".format(source.name, error_msg)
        if self.slack:
            utils.slack.publish(
                ALERT_MSG_CPC_CHANGES.format(details),
                msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                username=utils.slack.USER_AUTOPILOT,
            )
            return
        self._print(ALERT_MSG_CPC_CHANGES.format(details))
