import datetime

import utils.command_helpers

import dash.models
import dash.constants
import redshiftapi.db
import prodops.helpers

QUERY = "SELECT campaign_id, SUM(impressions) FROM mv_campaign WHERE date >= '{}' AND campaign_id IN ({}) GROUP BY campaign_id"


class Command(utils.command_helpers.ExceptionCommand):
    help = "Generate report of depleted budgets"

    def add_arguments(self, parser):
        parser.add_argument("--agency", dest="agency", default=None, help="Agency ID")
        parser.add_argument("--account", dest="account", default=None, help="Account ID")
        parser.add_argument("--campaign", dest="campaign", default=None, help="Campaign ID")

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        today = datetime.date.today()

        name = "stale-budgets_"
        campaigns = dash.models.Campaign.objects.all()
        if options.get("agency"):
            campaigns = campaigns.filter(account__agency_id=int(options["agency"]))
            name += "agency-{}_".format(options["agency"])
        elif options.get("account"):
            campaigns = campaigns.filter(account_id=int(options["account"]))
            name += "account-{}_".format(options["account"])
        elif options.get("campaign"):
            campaigns = campaigns.filter(pk=int(options["campaign"]))
            name += "campaign-{}_".format(options["campaign"])
        else:
            self._print("No lookup parameters")
            return
        name += str(today)

        campaign_ids = campaigns.values_list("id", flat=True)
        impressions = {}
        with redshiftapi.db.get_stats_cursor() as cur:
            cur.execute(QUERY.format(today - datetime.timedelta(3), ", ".join(map(str, campaign_ids))))
            impressions = dict(cur.fetchall())

        campaigns = campaigns.exclude(pk__in=[cid for cid, impr in impressions.items() if impr > 0])

        out = []
        for budget in dash.models.BudgetLineItem.objects.filter(
            end_date__gt=today, campaign_id__in=campaigns.values_list("id", flat=True)
        ).select_related("campaign"):
            total_spend = budget.get_available_etfm_amount()
            out.append(
                (
                    budget.campaign.pk,
                    budget.campaign.name,
                    budget.pk,
                    budget.end_date,
                    budget.amount,
                    total_spend,
                    budget.amount - total_spend,
                )
            )
        self._print(
            prodops.helpers.generate_report(
                name,
                [
                    (
                        "Campaign ID",
                        "Campaign name",
                        "Budget ID",
                        "Budget end date",
                        "Budget amount",
                        "Budget spend",
                        "Budget available",
                    )
                ]
                + out,
            )
        )
