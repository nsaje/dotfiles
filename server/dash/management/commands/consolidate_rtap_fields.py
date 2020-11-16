import logging

from django.db.models import Q
from django.db.models import Sum

import core.models
from dash import constants
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000

# TODO: RTAP: PR changes
# created dt filter
# dryrun total changed + print changes
# mode/pass only running
# mode unarchived exclude running
# mode archived


# TODO: RTAP: BACKFILL: remove after all agencies migrated
class Command(Z1Command):
    help = "Consolidate ad group bid and budget settings values"

    def add_arguments(self, parser):
        parser.add_argument(dest="agency_ids", type=int, nargs="+", help="IDs of migrated agencies")
        parser.add_argument("--batch-size", dest="batch_size", default=BATCH_SIZE, type=int, help="Batch size")

    def handle(self, *args, **options):
        agency_ids = options["agency_ids"]
        batch_size = options.get("batch_size", BATCH_SIZE)

        ad_groups_qs = core.models.AdGroup.objects.filter(
            Q(campaign__account__agency_id__in=agency_ids) & Q(campaign__account__agency__uses_realtime_autopilot=True)
        ).select_related("settings")

        for ag in ad_groups_qs.iterator(chunk_size=batch_size):

            new_max_ap_bid = (
                ag.settings.b1_sources_group_cpc
                if ag.bidding_type == constants.BiddingType.CPC
                else ag.settings.b1_sources_group_cpm
            )
            new_local_max_ap_bid = (
                ag.settings.local_b1_sources_group_cpc
                if ag.bidding_type == constants.BiddingType.CPC
                else ag.settings.local_b1_sources_group_cpm
            )

            if ag.settings.b1_sources_group_enabled:
                ag.settings.update_unsafe(
                    None,
                    daily_budget=ag.settings.b1_sources_group_daily_budget,
                    local_daily_budget=ag.settings.local_b1_sources_group_daily_budget,
                    autopilot_daily_budget=ag.settings.b1_sources_group_daily_budget,
                    local_autopilot_daily_budget=ag.settings.local_b1_sources_group_daily_budget,
                    cpc=ag.settings.b1_sources_group_cpc_cc,
                    local_cpc=ag.settings.local_b1_sources_group_cpc_cc,
                    cpm=ag.settings.b1_sources_group_cpm,
                    local_cpm=ag.settings.local_b1_sources_group_cpm,
                    max_autopilot_bid=new_max_ap_bid,
                    local_max_autopilot_bid=new_local_max_ap_bid,
                    write_history=False,
                )
            else:
                if ag.campaign.settings.autopilot:
                    logger.info(
                        "Found an ad group with managing sources separately and campaign autopilot turned on",
                        ad_group_id=ag.id,
                    )
                    continue

                ad_group_budget_data = ag.adgroupsource_set.filter_active().aggregate(
                    total_daily_budget=Sum("settings__daily_budget_cc"),
                    total_local_daily_budget=Sum("settings__local_daily_budget_cc"),
                )
                ag.settings.update_unsafe(
                    None,
                    daily_budget=ad_group_budget_data["total_daily_budget"],
                    local_daily_budget=ad_group_budget_data["total_local_daily_budget"],
                    autopilot_daily_budget=ad_group_budget_data["total_daily_budget"],
                    local_autopilot_daily_budget=ad_group_budget_data["total_local_daily_budget"],
                    max_autopilot_bid=new_max_ap_bid,
                    local_max_autopilot_bid=new_local_max_ap_bid,
                    write_history=False,
                )
