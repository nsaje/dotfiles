import utils.pagerduty_helper as pgdh
from dash.features.supply_reports.service import send_supply_reports
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    def add_arguments(self, parser):
        parser.add_argument("recipients", type=str, nargs="*", help="List of recipients")

        parser.add_argument(
            "--dry-run", dest="dry_run", action="store_true", help="Skip sending emails and updating last sent times."
        )
        parser.add_argument(
            "--skip-already-sent", dest="skip_sent", action="store_true", help="Only execute unsent recipients."
        )
        parser.add_argument(
            "--overwrite-recipients",
            type=str,
            nargs="?",
            dest="overwrite_recipients",
            help="Email to overwritte all recipient emails.",
        )

    @pgdh.catch_and_report_exception(
        pgdh.PagerDutyEventType.PRODOPS,
        summary="Z1 Supply Reports Issue",
        links={
            "https://confluence.outbrain.com/display/ZemantaProdops/ProdOps%3A+Exception+in+Z1+Job+-+Send+supply+report+emails": "Playbook"
        },
    )
    def handle(self, *args, **options):
        logger.info("Sending Supply Reports")
        send_supply_reports(
            recipient_ids=[int(rid) for rid in (options.get("recipients") or [])],
            dry_run=options.get("dry_run", False),
            skip_already_sent=options.get("skip_sent", False),
            overwrite_recipients_email=options.get("overwrite_recipients"),
        )
