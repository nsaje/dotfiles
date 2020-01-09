import datetime

from django.conf import settings

import dash.models
from utils import converters
from utils import pagerduty_helper
from utils import zlogging
from utils.command_helpers import Z1Command
from utils.command_helpers import parse_id_list

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Free recently inactive budget assets."

    def add_arguments(self, parser):
        parser.add_argument("--budget-ids", help="Budget line item IDs")
        parser.add_argument("--verbose", action="store_true", default=False, help="Verbose")

    def handle(self, *args, **options):
        today = datetime.date.today()
        budget_ids = set(parse_id_list(options, "budget_ids") or [])
        is_verbose = options.get("verbose", False)

        error_count = 0

        candidate_budgets = dash.models.BudgetLineItem.objects.filter(
            **(
                budget_ids
                and dict(pk__in=budget_ids)
                or dict(end_date__lt=today, end_date__gte=today - datetime.timedelta(settings.LAST_N_DAY_REPORTS + 1))
            )
        )

        for budget in candidate_budgets:
            if is_verbose:
                self.stdout.write("Processing {}\n".format(str(budget)))
            try:
                budget.free_inactive_allocated_assets()
                if is_verbose:
                    self.stdout.write(
                        "Budget has ${} assets freed.\n".format(budget.freed_cc * converters.CC_TO_DECIMAL_CURRENCY)
                    )
            except AssertionError:
                if is_verbose:
                    self.stdout.write("Assertion error: Budget status is {}.\n".format(budget.state_text()))
            except Exception:
                error_count += 1
                logger.exception(
                    "Failed freeing inactive allocated assets", budget_id=budget.id, campaign_id=budget.campaign.id
                )

        incident_key = __name__.split(".")[-1]

        if error_count > 0:
            pagerduty_helper.trigger(
                pagerduty_helper.PagerDutyEventType.PRODOPS,
                incident_key,
                "Job encountered {} errors. Please investigate!".format(error_count),
            )
        else:
            pagerduty_helper.resolve(
                pagerduty_helper.PagerDutyEventType.PRODOPS, incident_key, "Job encountered no errors."
            )
