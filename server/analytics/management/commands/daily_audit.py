import datetime
from decimal import Decimal

import analytics.delivery
import analytics.monitor
import analytics.statements
import dash.features.submission_filters.constants as sf_constants
import dash.models
import utils.command_helpers
import utils.csv_utils
import utils.email_helper
from server import settings

RECIPIENTS = (
    "zem-operations@outbrain.com",
    "prodops@outbrain.com",
    "oen-supply-team@outbrain.com",
    "zstopinsek@outbrain.com",
    "tadej.pavlic@zemanta.com",
)

VALID_PACING_ACCOUNT_TYPES = (
    dash.constants.AccountType.ACTIVATED,
    dash.constants.AccountType.MANAGED,
    dash.constants.AccountType.PILOT,
)

TRIPLELIFT_SOURCE_ID = 34


class Command(utils.command_helpers.Z1Command):
    help = "Daily audits"

    def add_arguments(self, parser):
        parser.add_argument("--verbose", dest="verbose", action="store_true", help="Display output")
        parser.add_argument("--send-emails", dest="send_emails", action="store_true", help="Send emails")

        parser.add_argument("--date", "-d", dest="date", help="Date checked (default yesterday)")
        parser.add_argument(
            "--min-pacing", dest="max_pacing", default=Decimal("50.0"), help="Threshold for alarm (default 0.8)"
        )
        parser.add_argument(
            "--min-ad-group-spend",
            dest="min_ag_spend",
            default=Decimal("10.0"),
            help="Threshold for alarm (default 0.8)",
        )
        parser.add_argument(
            "--max-pacing",
            dest="min_pacing",
            default=Decimal("200.0"),
            help="Threshold for alarm on first of month (default 0.6)",
        )
        parser.add_argument(
            "--days-running",
            dest="days_running",
            default=7,
            help="Minimal number of days that ad groups have to be running",
        )

    def _print(self, msg):
        if not self.verbose:
            return
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        self.send_emails = options["send_emails"]
        self.alarms = False
        self.email_body = ""

        self.audit_autopilot(options)
        self.audit_pilot_managed_running_ad_groups(options)
        self.audit_account_credits(options)
        self.audit_click_discrepancy(options)
        self.audit_cpc_vs_ecpc(options)
        self.audit_publishers_blacklisted(options)
        self.audit_submission_filters(options)

        if self.alarms and self.send_emails:
            utils.email_helper.send_internal_email(
                recipient_list=RECIPIENTS, subject="Daily audit", body=self.email_body
            )

    def audit_click_discrepancy(self, options):
        alarms = analytics.monitor.audit_click_discrepancy()
        if not alarms:
            return
        self.alarms = True
        title = "Campaigns with increased click discrepancy:"
        self._print(title)
        self.email_body += "<h3>{}</h3> \n".format(title)
        for campaign, base, new in alarms:
            text = " - {} ({}% -> {}%): {}".format(
                campaign.get_long_name(),
                base,
                new,
                "https://one.zemanta.com/v2/analytics/campaign/{}".format(campaign.pk),
            )
            self._print(text)
            self.email_body += text + "\n"
        self.email_body += "\n"

    def audit_account_credits(self, options):
        alarms = analytics.monitor.audit_account_credits()
        if not alarms:
            return
        self.alarms = True
        title = "Accounts with depleting credits:"
        self._print(title)
        self.email_body += "<h3>{}</h3> \n".format(title)
        for account in alarms:
            self._print("- {} {}".format(account.name, account.pk))
            self.email_body += " - {} {}\n".format(
                account.get_long_name(), "https://one.zemanta.com/v2/credit/account/{}".format(account.pk)
            )
        self.email_body += "\n"

    def audit_pilot_managed_running_ad_groups(self, options):
        alarms = analytics.monitor.audit_running_ad_groups(
            options["min_ag_spend"], (dash.constants.AccountType.MANAGED, dash.constants.AccountType.PILOT)
        )
        if not alarms:
            return
        self.alarms = True
        title = "Running pilot or managed ad groups with spend below ${}:".format(options["min_ag_spend"])
        self._print(title)
        self.email_body += "<h3>{}</h3> \n".format(title)
        for ad_group in alarms:
            self._print("- {} {}".format(ad_group.name, ad_group.pk))
            self.email_body += " - {} {}\n".format(
                ad_group.name, "https://one.zemanta.com/v2/analytics/adgroup/{}".format(ad_group.pk)
            )
        self.email_body += "\n"

    def audit_autopilot(self, options):
        ap_alarms = analytics.monitor.audit_autopilot_ad_groups()
        if not ap_alarms:
            return
        self.alarms = True
        self._print("Autopilot did not run on the following ad groups:")
        self.email_body += "<h3>Autopilot did not run on the following ad groups:</h3>\n"

        for ad_group in ap_alarms:
            self._print("- {} {}".format(ad_group.name, ad_group.pk))
            self.email_body += " - {} {}\n".format(
                ad_group.name, "https://one.zemanta.com/v2/analytics/adgroup/{}".format(ad_group.pk)
            )
        self.email_body += "\n"

    def audit_cpc_vs_ecpc(self, options):
        alarms = analytics.monitor.audit_bid_cpc_vs_ecpc()
        if not alarms:
            return
        self.alarms = True
        title = "Yesterday Ad groups with too high effective CPC comparing to their CPC:"
        self._print("{}\n".format(title))
        msg = ""
        for alarm in alarms:
            msg += """- Ad group <b>{name}</b> (https://one.zemanta.com/v2/analytics/adgroup/{ad_group_id}/sources) spent ${total_spend}
             with too high eCPC (${ecpc}) compared to its bid CPC (${cpc}) on <b>{source_name}</b>. \n""".format(
                **alarm
            )
        self._print(msg)
        self.email_body += "<h3>{}</h3>\n {}".format(title, msg)

    def audit_publishers_blacklisted(self, options):
        yesterday = datetime.date.today() - datetime.timedelta(1)
        blacklisted_yesterday = dash.models.PublisherGroupEntry.objects.filter(
            publisher_group__id=settings.GLOBAL_BLACKLIST_ID, modified_dt__contains=yesterday
        )
        if not blacklisted_yesterday:
            return
        title = "Publishers blacklisted yesterday:"
        msg = ["- Publisher '{}' was added to the global blacklist.".format(p.publisher) for p in blacklisted_yesterday]
        text = "\n".join(msg)
        self._print("{}\n   {}".format(title, text))
        self.email_body += "<h3>{}</h3> \n{}".format(title, text)

    def audit_submission_filters(self, options):
        yesterday = datetime.date.today() - datetime.timedelta(1)
        updated_yesterday = dash.models.SubmissionFilter.objects.filter(modified_dt__contains=yesterday).select_related(
            "source", "account", "agency", "campaign", "ad_group", "content_ad"
        )
        if not updated_yesterday:
            return

        title = "Submissions filter changed yesterday:"
        messages = [
            """- Submission filter #{id} state was set to '{state}' on source '{source}' for {agency}{account}{ad_group}{content_ad}""".format(
                id=sf.id,
                state=sf_constants.SubmissionFilterState.get_text(sf.state),
                source=sf.source,
                agency="agency '{}'.".format(sf.agency) if sf.agency else "",
                account="account '{}'.".format(sf.account) if sf.account else "",
                ad_group="ad group '{}'.".format(sf.ad_group) if sf.ad_group else "",
                content_ad="content ad '{}'.".format(sf.content_ad) if sf.content_ad else "",
            )
            for sf in updated_yesterday
        ]
        text = "\n".join(messages)
        self._print("\n".join([title, text]))
        self.email_body += "<h3>{}</h3>\n{}".format(title, text)
