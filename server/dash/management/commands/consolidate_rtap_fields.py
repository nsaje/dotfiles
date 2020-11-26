import concurrent.futures
import datetime
import decimal
import functools
import json
import logging
from collections import defaultdict

from django.db.models import Avg
from django.db.models import Case
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Coalesce

import core.models
import utils.decimal_helpers
import utils.list_helper
import utils.queryset_helper
from core.features import bid_modifiers
from dash import constants
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)

BID_PRECISION = decimal.Decimal("1.000")
BUDGET_PRECISION = decimal.Decimal("1.00")
DEFAULT_MODE = 1
BATCH_SIZE = 1000
POOL_SIZE = 1000


# TODO: RTAP: BACKFILL: remove after all agencies migrated
class Command(Z1Command):
    help = "Consolidate ad group bid and budget settings values"

    def add_arguments(self, parser):
        parser.add_argument(dest="agency_ids", type=int, nargs="+", help="IDs of migrated agencies")
        parser.add_argument(
            "--apply-changes", dest="apply_changes", action="store_true", help="Apply calculated changes"
        )
        parser.add_argument("--created_dt", type=datetime.datetime.fromisoformat, default=None)
        parser.add_argument(
            "--mode",
            type=int,
            default=DEFAULT_MODE,
            help="1: running only, 2: unarchived - running, 3: archived, 4: all",
        )
        parser.add_argument("--batch-size", dest="batch_size", default=BATCH_SIZE, type=int, help="Batch size")
        parser.add_argument("--use-pool", dest="use_pool", action="store_true", help="Use thread pool")
        parser.add_argument("--pool-size", dest="pool_size", type=int, default=POOL_SIZE, help="Thread pool size")

    def handle(self, *args, **options):
        agency_ids = options["agency_ids"]
        apply_changes = options.get("apply_changes", False)
        created_dt = options.get("created_dt", None)
        mode = options.get("mode", DEFAULT_MODE)
        batch_size = options.get("batch_size", BATCH_SIZE)
        use_pool = options.get("use_pool", False)
        pool_size = options.get("pool_size", POOL_SIZE)

        if use_pool:
            self.stdout.write(self.style.SUCCESS("Processing using thread pool"))

        if apply_changes:
            self.stdout.write(self.style.WARNING("The changes will be applied to database"))

        no_changes_counters = defaultdict(int)
        changes_counters = defaultdict(int)

        ad_groups_qs = core.models.AdGroup.objects.filter(
            campaign__account__agency_id__in=agency_ids, campaign__account__agency__uses_realtime_autopilot=True
        )

        if created_dt:
            ad_groups_qs = ad_groups_qs.filter(created_dt__gte=created_dt)

        if mode == 1:
            ad_groups_qs = ad_groups_qs.filter_running()
        elif mode == 2:
            ad_groups_qs = ad_groups_qs.filter(archived=False).exclude(
                id__in=ad_groups_qs.filter_running().values_list("id", flat=True)
            )
        elif mode == 3:
            ad_groups_qs = ad_groups_qs.filter(archived=True)

        ad_group_ids = list(ad_groups_qs.values_list("id", flat=True))

        ad_group_count = len(ad_group_ids)
        self.stdout.write(self.style.SUCCESS("Found %s ad groups to process" % ad_group_count))
        batch_id = 0
        for ids_chunk in utils.list_helper.list_chunker(ad_group_ids, batch_size):
            progress = 100.0 * (batch_id * batch_size) / ad_group_count
            self.stdout.write("Progress: %.2f %%" % progress)
            batch_id += 1

            ad_groups_qs = (
                core.models.AdGroup.objects.filter(id__in=ids_chunk)
                .select_related("settings")
                .annotate(
                    avg_bid=Coalesce(
                        Case(
                            When(
                                Q(bidding_type=constants.BiddingType.CPC, settings__b1_sources_group_enabled=True),
                                then=Avg("adgroupsource__settings__cpc_cc"),
                            ),
                            When(
                                Q(bidding_type=constants.BiddingType.CPM, settings__b1_sources_group_enabled=True),
                                then=Avg("adgroupsource__settings__cpm"),
                            ),
                            default=Value(0.0),
                        ),
                        Value(0.0),
                    ),
                    total_daily_budget=Coalesce(
                        Case(
                            When(
                                settings__b1_sources_group_enabled=False,
                                then=Sum(
                                    Coalesce(
                                        Case(
                                            When(
                                                adgroupsource__settings__state=constants.AdGroupSourceSettingsState.ACTIVE,
                                                then=F("adgroupsource__settings__daily_budget_cc"),
                                            ),
                                            default=Value(0.0),
                                        ),
                                        Value(0.0),
                                    )
                                ),
                            ),
                            default=Value(0.0),
                        ),
                        Value(0.0),
                    ),
                    total_local_daily_budget=Coalesce(
                        Case(
                            When(
                                settings__b1_sources_group_enabled=False,
                                then=Sum(
                                    Coalesce(
                                        Case(
                                            When(
                                                adgroupsource__settings__state=constants.AdGroupSourceSettingsState.ACTIVE,
                                                then=F("adgroupsource__settings__local_daily_budget_cc"),
                                            ),
                                            default=Value(0.0),
                                        ),
                                        Value(0.0),
                                    )
                                ),
                            ),
                            default=Value(0.0),
                        ),
                        Value(0.0),
                    ),
                )
            )

            if use_pool:
                with concurrent.futures.ThreadPoolExecutor(max_workers=pool_size) as executor:
                    results = executor.map(
                        functools.partial(self._process_ad_group, apply_changes=apply_changes), ad_groups_qs
                    )

                    for counter_to_update, changes in results:
                        if changes:
                            changes_counters[counter_to_update] += 1
                        else:
                            no_changes_counters[counter_to_update] += 1
            else:
                for ag in ad_groups_qs:
                    counter_to_update, changes = self._process_ad_group(ag, apply_changes=apply_changes)
                    if changes:
                        changes_counters[counter_to_update] += 1
                    else:
                        no_changes_counters[counter_to_update] += 1

        self.stdout.write("Changes counters:\n" + json.dumps(changes_counters, indent=2))
        self.stdout.write("No changes counters:\n" + json.dumps(no_changes_counters, indent=2))
        self.stdout.write(
            self.style.SUCCESS(
                "Processed %s ad groups" % (sum(changes_counters.values()) + sum(no_changes_counters.values()))
            )
        )

    def _process_ad_group(self, ag, apply_changes=False):
        changes = False
        counter_to_update = ""

        delete_source_bid_modifiers = False

        new_budget = ag.settings.b1_sources_group_daily_budget
        new_local_budget = ag.settings.local_b1_sources_group_daily_budget

        new_cpc = ag.settings.cpc
        new_local_cpc = ag.settings.local_cpc
        new_cpm = ag.settings.cpm
        new_local_cpm = ag.settings.local_cpm

        uses_autopilot = ag.settings.autopilot_state != constants.AdGroupSettingsAutopilotState.INACTIVE

        if ag.settings.b1_sources_group_enabled:
            if uses_autopilot:
                if ag.bidding_type == constants.BiddingType.CPC:
                    if ag.settings.cpc is None:
                        # don't need to update the new cpc values
                        counter_to_update = "group:autopilot_on:unlimited_bid:cpc"
                    elif utils.decimal_helpers.equal_decimals(
                        ag.settings.local_cpc, ag.settings.local_b1_sources_group_cpc_cc, precision=BID_PRECISION
                    ):
                        new_cpc = ag.settings.max_autopilot_bid
                        new_local_cpc = ag.settings.local_max_autopilot_bid
                        counter_to_update = "group:autopilot_on:equal_bids:cpc"
                    else:
                        if _should_use_b1_sources_group_bid(
                            decimal.Decimal(ag.avg_bid), ag.settings.cpc, ag.settings.b1_sources_group_cpc_cc
                        ):
                            new_cpc = ag.settings.b1_sources_group_cpc_cc
                            new_local_cpc = ag.settings.local_b1_sources_group_cpc_cc
                            counter_to_update = "group:autopilot_on:use_b1_group_bid:cpc"
                        else:
                            # don't need to update the new cpc values
                            counter_to_update = "group:autopilot_on:use_ad_group_bid:cpc"
                else:
                    if ag.settings.cpm is None:
                        # don't need to update the new cpm values
                        counter_to_update = "group:autopilot_on:unlimited_bid:cpm"
                    elif utils.decimal_helpers.equal_decimals(
                        ag.settings.local_cpm, ag.settings.local_b1_sources_group_cpm, precision=BID_PRECISION
                    ):
                        new_cpm = ag.settings.max_autopilot_bid
                        new_local_cpm = ag.settings.local_max_autopilot_bid
                        counter_to_update = "group:autopilot_on:equal_bids:cpm"
                    else:
                        if _should_use_b1_sources_group_bid(
                            decimal.Decimal(ag.avg_bid), ag.settings.cpm, ag.settings.b1_sources_group_cpm
                        ):
                            new_cpm = ag.settings.b1_sources_group_cpm
                            new_local_cpm = ag.settings.local_b1_sources_group_cpm
                            counter_to_update = "group:autopilot_on:use_b1_group_bid:cpm"
                        else:
                            # don't need to update the new cpm values
                            counter_to_update = "group:autopilot_on:use_ad_group_bid:cpm"
            else:
                if ag.bidding_type == constants.BiddingType.CPC:
                    if ag.settings.cpc is None:
                        # don't need to update the new cpc values
                        counter_to_update = "group:autopilot_off:unlimited_bid:cpc"
                    elif utils.decimal_helpers.equal_decimals(
                        ag.settings.local_cpc, ag.settings.local_b1_sources_group_cpc_cc, precision=BID_PRECISION
                    ):
                        # don't need to update the new cpc values
                        counter_to_update = "group:autopilot_off:equal_bids:cpc"
                    else:
                        if utils.decimal_helpers.equal_decimals(
                            ag.avg_bid, ag.settings.b1_sources_group_cpc_cc, precision=BID_PRECISION
                        ):
                            new_cpc = ag.settings.b1_sources_group_cpc_cc
                            new_local_cpc = ag.settings.local_b1_sources_group_cpc_cc
                            # set delete SBMs flag
                            delete_source_bid_modifiers = True
                            counter_to_update = "group:autopilot_off:use_b1_group_bid:cpc"
                        else:
                            # don't need to update the new cpc values
                            counter_to_update = "group:autopilot_off:use_ad_group_bid:cpc"
                else:
                    if ag.settings.cpm is None:
                        # don't need to update the new cpm values
                        counter_to_update = "group:autopilot_off:unlimited_bid:cpm"
                    elif utils.decimal_helpers.equal_decimals(
                        ag.settings.local_cpm, ag.settings.local_b1_sources_group_cpm, precision=BID_PRECISION
                    ):
                        # don't need to update the new cpm values
                        counter_to_update = "group:autopilot_off:equal_bids:cpm"
                    else:
                        if utils.decimal_helpers.equal_decimals(
                            ag.avg_bid, ag.settings.b1_sources_group_cpm, precision=BID_PRECISION
                        ):
                            new_cpm = ag.settings.b1_sources_group_cpm
                            new_local_cpm = ag.settings.local_b1_sources_group_cpm
                            # set delete SMBs flag
                            delete_source_bid_modifiers = True
                            counter_to_update = "group:autopilot_off:use_b1_group_bid:cpm"
                        else:
                            # don't need to update the new cpm values
                            counter_to_update = "group:autopilot_off:use_ad_group_bid:cpm"

        else:
            new_budget = decimal.Decimal(ag.total_daily_budget).quantize(decimal.Decimal("1.0000"))
            new_local_budget = decimal.Decimal(ag.total_local_daily_budget).quantize(decimal.Decimal("1.0000"))

            if ag.bidding_type == constants.BiddingType.CPC:
                new_cpc = ag.settings.max_autopilot_bid if uses_autopilot else ag.settings.cpc
                new_local_cpc = ag.settings.local_max_autopilot_bid if uses_autopilot else ag.settings.local_cpc

                if uses_autopilot:
                    counter_to_update = "separately:autopilot_on:use_ad_group_bid:cpc"
                else:
                    counter_to_update = "separately:autopilot_off:use_ad_group_bid:cpc"
            else:
                new_cpm = ag.settings.max_autopilot_bid if uses_autopilot else ag.settings.cpm
                new_local_cpm = ag.settings.local_max_autopilot_bid if uses_autopilot else ag.settings.local_cpm

                if uses_autopilot:
                    counter_to_update = "separately:autopilot_on:use_ad_group_bid:cpm"
                else:
                    counter_to_update = "separately:autopilot_off:use_ad_group_bid:cpm"

        new_autopilot_bid = new_cpc if ag.bidding_type == constants.BiddingType.CPC else new_cpm
        new_local_autopilot_bid = new_local_cpc if ag.bidding_type == constants.BiddingType.CPC else new_local_cpm

        if not all(
            _equal_values(a, b, p)
            for a, b, p in [
                (ag.settings.daily_budget, new_budget, BUDGET_PRECISION),
                (ag.settings.local_daily_budget, new_local_budget, BUDGET_PRECISION),
                (ag.settings.autopilot_daily_budget, new_budget, BUDGET_PRECISION),
                (ag.settings.local_autopilot_daily_budget, new_local_budget, BUDGET_PRECISION),
                (ag.settings.b1_sources_group_daily_budget, new_budget, BUDGET_PRECISION),
                (ag.settings.local_b1_sources_group_daily_budget, new_local_budget, BUDGET_PRECISION),
                (ag.settings.cpc, new_cpc, BID_PRECISION),
                (ag.settings.local_cpc, new_local_cpc, BID_PRECISION),
                (ag.settings.cpm, new_cpm, BID_PRECISION),
                (ag.settings.local_cpm, new_local_cpm, BID_PRECISION),
                (ag.settings.b1_sources_group_cpc_cc, new_cpc, BID_PRECISION),
                (ag.settings.local_b1_sources_group_cpc_cc, new_local_cpc, BID_PRECISION),
                (ag.settings.b1_sources_group_cpm, new_cpm, BID_PRECISION),
                (ag.settings.local_b1_sources_group_cpm, new_local_cpm, BID_PRECISION),
                (ag.settings.max_autopilot_bid, new_autopilot_bid, BID_PRECISION),
                (ag.settings.local_max_autopilot_bid, new_local_autopilot_bid, BID_PRECISION),
            ]
        ):
            changes = True

        if changes and apply_changes:
            new_budget = _trim_precision(new_budget, BUDGET_PRECISION)
            new_local_budget = _trim_precision(new_local_budget, BUDGET_PRECISION)
            new_cpc = _trim_precision(new_cpc, BID_PRECISION)
            new_local_cpc = _trim_precision(new_local_cpc, BID_PRECISION)
            new_cpm = _trim_precision(new_cpm, BID_PRECISION)
            new_autopilot_bid = _trim_precision(new_autopilot_bid, BID_PRECISION)
            new_local_autopilot_bid = _trim_precision(new_local_autopilot_bid, BID_PRECISION)

            ag.settings.update_unsafe(
                None,
                daily_budget=new_budget,
                local_daily_budget=new_local_budget,
                autopilot_daily_budget=new_budget,
                local_autopilot_daily_budget=new_local_budget,
                b1_sources_group_daily_budget=new_budget,
                local_b1_sources_group_daily_budget=new_local_budget,
                cpc=new_cpc,
                local_cpc=new_local_cpc,
                cpm=new_cpm,
                local_cpm=new_local_cpm,
                b1_sources_group_cpc_cc=new_cpc,
                local_b1_sources_group_cpc_cc=new_local_cpc,
                b1_sources_group_cpm=new_cpm,
                local_b1_sources_group_cpm=new_local_cpm,
                max_autopilot_bid=new_autopilot_bid,
                local_max_autopilot_bid=new_local_autopilot_bid,
                write_history=False,
            )
            if delete_source_bid_modifiers:
                ag.bidmodifier_set.filter(type=bid_modifiers.BidModifierType.SOURCE).delete()

        return counter_to_update, changes


def _should_use_b1_sources_group_bid(avg_bid, ad_group_bid, b1_sources_group_bid):
    return abs(avg_bid - b1_sources_group_bid) < abs(avg_bid - ad_group_bid)


def _equal_values(v1, v2, precision):
    if v1 is None or v2 is None:
        return v1 == v2

    return utils.decimal_helpers.equal_decimals(v1, v2, precision=precision)


def _trim_precision(decimal_value, precision):
    if decimal_value is None:
        return None

    return decimal_value.quantize(precision)
