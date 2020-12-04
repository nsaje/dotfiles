import concurrent.futures

from django.db.models import Q

import core.models
import dash.constants
import utils.queryset_helper
from core.features import bid_modifiers
from utils.command_helpers import Z1Command

POOL_SIZE = 10
BATCH_SIZE = 2000


# TODO: RTAP: remove after SMBs have been reset
class Command(Z1Command):
    help = "Reset real-time autopilot AdGroup source bid modifiers and write a history record about the change"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply-changes", dest="apply_changes", action="store_true", help="Apply calculated changes"
        )
        parser.add_argument("--pool-size", dest="pool_size", type=int, default=POOL_SIZE, help="Thread pool size")
        parser.add_argument("--batch-size", dest="batch_size", default=BATCH_SIZE, type=int, help="Batch size")

    def handle(self, *args, **options):
        apply_changes = options.get("apply_changes", False)
        pool_size = options.get("pool_size", POOL_SIZE)
        batch_size = options.get("batch_size", BATCH_SIZE)

        ad_group_ids = list(
            core.models.AdGroup.objects.filter(
                Q(campaign__account__agency__isnull=False)
                & Q(campaign__account__agency__uses_realtime_autopilot=True)
                & ~Q(settings__autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
            ).values_list("id", flat=True)
        )

        bid_modifiers_qs = bid_modifiers.BidModifier.objects.filter(type=bid_modifiers.BidModifierType.SOURCE).filter(
            ad_group_id__in=ad_group_ids
        )

        ad_group_count = len(ad_group_ids)
        self.stdout.write(self.style.SUCCESS("Found %s ad groups to process" % len(ad_group_ids)))

        if not apply_changes:
            self.stdout.write(self.style.SUCCESS("Found %s source bid modifiers to delete" % bid_modifiers_qs.count()))
            return

        count, _ = bid_modifiers_qs.delete()
        self.stdout.write(self.style.SUCCESS("Deleted %s source bid modifiers" % count))

        batch_id = 0
        for ad_group_chunk in utils.queryset_helper.chunk_iterator(
            core.models.AdGroup.objects.filter(id__in=ad_group_ids), chunk_size=batch_size
        ):
            progress = 100.0 * (batch_id * batch_size) / ad_group_count
            self.stdout.write("Progress: %.2f %%" % progress)
            batch_id += 1

            with concurrent.futures.ThreadPoolExecutor(max_workers=pool_size) as executor:
                executor.map(self._write_history_log, ad_group_chunk)

    def _write_history_log(self, ad_group):
        ad_group.write_history(
            "As a result of the migration to the new Autopilot bidding strategy, bid modifiers on all media sources have been set to 0%. You are now able to edit them manually."
        )
