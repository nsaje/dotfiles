import datetime

import utils.slack
from etl import nas_cpc_billing
from prodops import hacks
from utils.command_helpers import Z1Command

MESSAGE = "Adgroup #{ad_group_id} have its eCPC ({ecpc}) different from its CPC ({cpc})."


class Command(Z1Command):
    help = "Calculate billing cost for CPC goal bidding agencies."

    def add_arguments(self, parser):
        parser.add_argument("agency_id", type=int, help="An ID from a agency running NAS with CPC billing.")
        parser.add_argument(
            "--from",
            type=str,
            default=3,
            help="Start of the billing period to process. Date ('%Y-%m-%d') or number of days to process.",
        )
        parser.add_argument("--until", type=str, help="End date of the billing period to process.")
        parser.add_argument("--slack", action="store_true", help="Post discrepency message on Slack.")

    def handle(self, *args, **options):
        self.slack = options["slack"]

        if options.get("until"):
            until = datetime.datetime.strptime(options["until"], "%Y-%m-%d").date()
        else:
            until = datetime.date.today()
        try:
            since = datetime.datetime.strptime(options["from"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            delta = int(options["from"])
            since = until - datetime.timedelta(days=delta)

        if since > until:
            raise ValueError("Starting date '{}' must be before the end date '{}'".format(since, until))
        agency_id = options.get("agency_id")
        if agency_id not in hacks.CPC_GOAL_TO_BID_AGENCIES:
            raise ValueError(
                "'{}' is not a Native Ad Server CPC billing customer. Valid IDs are : {}".format(
                    agency_id, hacks.CPC_GOAL_TO_BID_AGENCIES
                )
            )
        nas_cpc_billing.process_cpc_billing(since, until, agency_id)

        discrepancies = nas_cpc_billing.check_discrepancy(since, until)
        if discrepancies:
            messages = [MESSAGE.format(**disc) for disc in discrepancies]
            text = "\n".join(messages)

            if self.slack:
                try:
                    utils.slack.publish(
                        text,
                        channel=utils.slack.CHANNEL_ALERTS_RND_PRODOPS,
                        username=utils.slack.USER_NAS_CPC_BILLING,
                        msg_type=utils.slack.MESSAGE_TYPE_WARNING,
                    )
                except Exception as e:
                    raise e

            self.stdout.write(text)
