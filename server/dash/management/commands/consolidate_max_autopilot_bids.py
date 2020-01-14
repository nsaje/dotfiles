import datetime

from django.db.models import Q

from dash import constants
from dash import models
from utils.command_helpers import Z1Command

BATCH_SIZE = 1000


class Command(Z1Command):
    help = "Consolidate (verify and fix) max autopilot bid settings values"

    def add_arguments(self, parser):
        parser.add_argument("--cutoff_date", type=datetime.datetime.fromisoformat, default=None)
        parser.add_argument("--fix", dest="fix", action="store_true", help="Fix discovered discrepancies")
        parser.add_argument("--batch-size", dest="batch_size", default=BATCH_SIZE, type=int, help="Batch size")

    def handle(self, *args, **options):
        cutoff = options.get("cutoff_date", None)
        fix = options.get("fix", False)
        batch_size = options.get("batch_size", BATCH_SIZE)

        self.consolidate_max_autopilot_bids(cutoff, batch_size, fix)

    def consolidate_max_autopilot_bids(self, cutoff, batch_size, fix):
        ag_qs = models.AdGroup.objects.exclude(
            Q(bidding_type=constants.BiddingType.CPC, settings__cpc_cc=None)
            | Q(bidding_type=constants.BiddingType.CPM, settings__max_cpm=None)
        )

        if cutoff is not None:
            ag_qs = ag_qs.filter(created_dt__gte=cutoff)

        ag_qs = ag_qs.values(
            "id",
            "bidding_type",
            "settings__cpc_cc",
            "settings__local_cpc_cc",
            "settings__max_cpm",
            "settings__local_max_cpm",
            "settings__max_autopilot_bid",
            "settings__local_max_autopilot_bid",
        )

        updated_count = 0

        for ag in ag_qs.iterator(chunk_size=batch_size):
            if ag["bidding_type"] == constants.BiddingType.CPC:
                if (
                    ag["settings__cpc_cc"] != ag["settings__max_autopilot_bid"]
                    or ag["settings__local_cpc_cc"] != ag["settings__local_max_autopilot_bid"]
                ):
                    updated_count += 1
                    if fix:
                        ad_group = models.AdGroup.objects.get(id=ag["id"])
                        ad_group.settings.update_unsafe(
                            None,
                            write_history=False,
                            **{
                                "max_autopilot_bid": ag["settings__cpc_cc"],
                                "local_max_autopilot_bid": ag["settings__local_cpc_cc"],
                            }
                        )
            else:
                if (
                    ag["settings__max_cpm"] != ag["settings__max_autopilot_bid"]
                    or ag["settings__local_max_cpm"] != ag["settings__local_max_autopilot_bid"]
                ):
                    updated_count += 1
                    if fix:
                        ad_group = models.AdGroup.objects.get(id=ag["id"])
                        ad_group.settings.update_unsafe(
                            None,
                            write_history=False,
                            **{
                                "max_autopilot_bid": ag["settings__max_cpm"],
                                "local_max_autopilot_bid": ag["settings__local_max_cpm"],
                            }
                        )

        if updated_count > 0:
            if fix:
                self.stdout.write(self.style.SUCCESS("Fixed {} ad groups.".format(updated_count)))
            else:
                self.stdout.write(self.style.WARNING("Found {} ad groups that need to be fixed.".format(updated_count)))
        else:
            self.stdout.write(self.style.SUCCESS("No ad groups need to be fixed!"))
