import datetime
import sys

import automation.campaignstop

from utils.command_helpers import ExceptionCommand
from utils import dates_helper
from utils import slack


class Command(ExceptionCommand):
    def add_arguments(self, parser):
        parser.add_argument("--date", "-d", dest="date", default=None, help="Date checked (default yesterday)")
        parser.add_argument("--slack", dest="slack", action="store_true", help="Notify via slack")
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")

    def handle(self, *args, **options):
        self._init_options(options)
        self._audit_stopped_campaigns()

    def _init_options(self, options):
        self.slack = options["slack"]
        self.verbose = options["verbose"]

        self.date = dates_helper.local_yesterday()
        if options["date"]:
            self.date = datetime.datetime.strptime(options["date"], "%Y-%m-%d").date()

    def _audit_stopped_campaigns(self):
        campaigns = automation.campaignstop.audit_stopped_campaigns(self.date)
        if not campaigns:
            return

        if self.slack:
            slack.publish(
                self._get_message_body(campaigns, output_type="slack"),
                msg_type=slack.MESSAGE_TYPE_INFO,
                username="Real-time campaign stop monitor",
            )
            slack.publish(
                self._get_message_body(campaigns, output_type="slack"),
                msg_type=slack.MESSAGE_TYPE_INFO,
                username="Real-time campaign stop monitor",
                channel="z1-monitor-campstop",
            )

        if self.verbose:
            sys.stdout.write(self._get_message_body(campaigns, output_type="verbose"))
            sys.stdout.flush()

    def _get_message_body(self, campaigns, *, output_type):
        message_parts = []
        stopped_by_end_date_count = 0
        stopped_by_end_date_overspend = 0
        for campaign, data in campaigns.items():
            if not data["active_budgets"]:
                stopped_by_end_date_count += 1
                if data["overspend"] and data["overspend"] >= 0.01:
                    stopped_by_end_date_overspend += data["overspend"]
                continue

            message_part = self._get_campaign_part(campaign, output_type=output_type)
            message_part += "${} remaining budget".format(data["available"])
            if data["overspend"] and data["overspend"] >= 0.01:
                message_part += self._get_overspend_part(data["overspend"], output_type=output_type)
            message_parts.append(message_part)

        message = self._get_message_title() + "\n".join(message_parts + [""])
        if stopped_by_end_date_count:
            message += "\nAdditionally, {} campaigns were stopped by end date - no active budgets left".format(
                "*" + str(stopped_by_end_date_count) + "*" if output_type == "slack" else stopped_by_end_date_count
            )
            if stopped_by_end_date_overspend:
                message += self._get_overspend_part(stopped_by_end_date_overspend, output_type=output_type)
        return message

    def _get_campaign_part(self, campaign, *, output_type):
        if output_type == "slack":
            return self._get_campaign_part_slack(campaign)
        return self._get_campaign_part_verbose(campaign)

    def _get_overspend_part(self, amount, *, output_type):
        if output_type == "slack":
            return " (*${:.2f} overspend*)".format(amount)
        return " (${:.2f} overspend)".format(amount)

    def _get_campaign_part_slack(self, campaign):
        return "- {}: ".format(slack.campaign_url(campaign))

    def _get_campaign_part_verbose(self, campaign):
        return "- {} ({}): ".format(campaign.name, campaign.id)

    def _get_message_title(self):
        if self.date == dates_helper.local_yesterday():
            date_str = "yesterday"
        else:
            date_str = "on " + self.date.isoformat()
        return "Campaigns stopped {}:\n".format(date_str)
