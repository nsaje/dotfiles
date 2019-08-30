import datetime
from decimal import Decimal

from django.db.models import Case
from django.db.models import CharField
from django.db.models import F
from django.db.models import Max
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models import When
from django.db.models.functions import Cast
from django.db.models.functions import StrIndex

from core.features import bid_modifiers
from dash import constants
from dash import models
from utils.command_helpers import Z1Command
from utils.queryset_helper import chunk_iterator

BATCH_SIZE = 1000
MAX_CPC = Decimal("20.0000")
MAX_CPM = Decimal("25.0000")


class Command(Z1Command):
    help = "Consolidate (verify and fix) changes done by source bid modifier migrations"

    def add_arguments(self, parser):
        parser.add_argument("cutoff_date", type=datetime.datetime.fromisoformat)
        parser.add_argument("--fix", dest="fix", action="store_true", help="Fix discovered discrepancies")
        parser.add_argument(
            "--only-ad-groups",
            dest="only_ad_groups",
            action="store_true",
            help="Only process discrepancies for ad groups",
        )
        parser.add_argument(
            "--only-bid-modifiers",
            dest="only_bid_modifiers",
            action="store_true",
            help="Only process discrepancies for bid modifiers",
        )
        parser.add_argument("--batch-size", dest="batch_size", default=BATCH_SIZE, type=int, help="Batch size")

    def handle(self, *args, **options):
        cutoff = options.get("cutoff_date")
        fix = options.get("fix", False)
        only_ad_groups = options.get("only_ad_groups", False)
        only_bid_modifiers = options.get("only_bid_modifiers", False)
        batch_size = options.get("batch_size", BATCH_SIZE)

        if all((only_ad_groups, only_bid_modifiers)):
            self.stdout.write(
                self.style.ERROR("Only one of --only-ad-groups and --only-bid-modifiers can be provided at a time")
            )

        if not only_bid_modifiers:
            self.consolidate_ad_groups(cutoff, batch_size, fix)
        if not only_ad_groups:
            self.consolidate_source_bid_modifiers(cutoff, batch_size, fix)

    def consolidate_ad_groups(self, cutoff, batch_size, fix):
        update_list = list(
            models.AdGroup.objects.filter(created_dt__gte=cutoff)
            .filter(Q(settings__cpc=None) | Q(settings__cpm=None))
            .values_list("id", flat=True)
        )

        if update_list:
            self.stdout.write(self.style.WARNING("Found {} ad groups that need to be fixed.".format(len(update_list))))

            if fix:
                self.fix_ad_groups(update_list, batch_size)
                self.stdout.write(self.style.SUCCESS("Fixed {} ad groups.".format(len(update_list))))

        else:
            self.stdout.write(self.style.SUCCESS("No ad groups need to be fixed!"))

    def fix_ad_groups(self, ad_group_ids, batch_size):
        ag_qs = models.AdGroup.objects.filter(id__in=ad_group_ids).values(
            "id",
            "bidding_type",
            "campaign__id",
            "campaign__account__currency",
            "settings__autopilot_state",
            "settings__cpc_cc",
            "settings__max_cpm",
            ad_group_mobile_idx=StrIndex("settings__target_devices", models.Value("mobile")),
            campaign_mobile_idx=StrIndex("campaign__settings__target_devices", models.Value("mobile")),
            max_adgroupsource_settings__cpc_cc=Max("adgroupsource__settings__cpc_cc"),
            max_adgroupsource_settings__cpm=Max("adgroupsource__settings__cpm"),
            max_source_default_cpc_cc=Max("adgroupsource__source__default_cpc_cc"),
            max_source_default_cpm=Max("adgroupsource__source__default_cpm"),
            max_source_default_mobile_cpc_cc=Max("adgroupsource__source__default_mobile_cpc_cc"),
            max_source_default_mobile_cpm=Max("adgroupsource__source__default_mobile_cpm"),
        )

        batch_number = 1

        for values in chunk_iterator(ag_qs, chunk_size=batch_size):
            self.stdout.write("Fixing ad group batch #%s" % batch_number)
            batch_number += 1

            goal_map = {}
            for cgv in (
                models.CampaignGoalValue.objects.filter(
                    campaign_goal__campaign__id__in=set(e["campaign__id"] for e in values),
                    campaign_goal__type=constants.CampaignGoalKPI.CPC,
                )
                .values("value", "campaign_goal__campaign__id")
                .distinct("campaign_goal__campaign__id")
                .order_by("campaign_goal__campaign__id", "-created_dt")
            ):
                goal_map[cgv["campaign_goal__campaign__id"]] = cgv["value"]

            currency_qs = (
                models.CurrencyExchangeRate.objects.filter(
                    currency__in=set(e["campaign__account__currency"] for e in values)
                )
                .values("currency", "exchange_rate")
                .distinct("currency")
                .order_by("currency", "-date")
            )
            currency_exchange_map = {e["currency"]: e["exchange_rate"] for e in currency_qs}

            for value in values:
                canditate_cpcs = []
                canditate_cpms = []
                if value["settings__autopilot_state"] in (
                    constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
                    constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
                ):
                    canditate_cpcs.append(Decimal("20.0000"))
                    canditate_cpms.append(Decimal("25.0000"))
                if value["ad_group_mobile_idx"] != 0 or value["campaign_mobile_idx"] != 0:
                    if value["max_source_default_mobile_cpc_cc"] is not None:
                        canditate_cpcs.append(value["max_source_default_mobile_cpc_cc"])
                    if value["max_source_default_mobile_cpm"] is not None:
                        canditate_cpms.append(value["max_source_default_mobile_cpm"])
                if value["max_adgroupsource_settings__cpc_cc"]:
                    canditate_cpcs.append(value["max_adgroupsource_settings__cpc_cc"])
                if value["max_adgroupsource_settings__cpm"]:
                    canditate_cpms.append(value["max_adgroupsource_settings__cpm"])
                if value["max_source_default_cpc_cc"]:
                    canditate_cpcs.append(value["max_source_default_cpc_cc"])
                if value["max_source_default_cpm"]:
                    canditate_cpms.append(value["max_source_default_cpm"])

                if value["campaign__id"] in goal_map:
                    canditate_cpcs.append(goal_map[value["campaign__id"]])

                if not canditate_cpcs:
                    canditate_cpcs.append(Decimal("1.0000"))
                if not canditate_cpms:
                    canditate_cpms.append(Decimal("1.0000"))

                update_kwargs = {}
                if value["settings__cpc_cc"] is None:
                    cpc = max(canditate_cpcs)
                    update_kwargs["cpc"] = cpc
                    update_kwargs["local_cpc"] = _to_local_currency(
                        cpc, currency_exchange_map[value["campaign__account__currency"]]
                    )
                if value["settings__max_cpm"] is None:
                    cpm = max(canditate_cpms)
                    update_kwargs["cpm"] = cpm
                    update_kwargs["local_cpm"] = _to_local_currency(
                        cpm, currency_exchange_map[value["campaign__account__currency"]]
                    )

                ad_group = models.AdGroup.objects.get(id=value["id"])
                ad_group.settings.update_unsafe(None, write_history=False, **update_kwargs)

    def consolidate_source_bid_modifiers(self, cutoff, batch_size, fix):
        create_count = 0
        update_count = 0

        sbm_qs = models.BidModifier.objects.filter(
            ad_group__id=OuterRef("id"), type=bid_modifiers.BidModifierType.SOURCE, target=OuterRef("source_id")
        )

        qs = (
            models.AdGroup.objects.filter(settings__created_dt__gte=cutoff)
            .exclude(Q(settings__cpc=None) | Q(settings__cpm=None))
            .annotate(
                cpc=F("settings__cpc"),
                cpm=F("settings__cpm"),
                source_id=Cast("adgroupsource__source__id", CharField()),
                source_cpc=F("adgroupsource__settings__cpc_cc"),
                source_cpm=F("adgroupsource__settings__local_cpm"),
                modifier_id=Subquery(sbm_qs.values_list("id", flat=True)[:1]),
                modifier=Subquery(sbm_qs.values_list("modifier", flat=True)[:1]),
            )
            .values(
                "id", "bidding_type", "cpc", "cpm", "source_id", "source_cpc", "source_cpm", "modifier_id", "modifier"
            )
        )

        batch_number = 1

        for chunk in chunk_iterator(qs, chunk_size=batch_size):
            self.stdout.write("Processing bid modifier batch #%s" % batch_number)
            batch_number += 1

            create_list = []
            update_list = []

            for elm in chunk:
                if elm["source_id"] is None:
                    # ad group has no sources
                    continue

                if elm["bidding_type"] == constants.BiddingType.CPC:
                    if elm["cpc"] is None:
                        self.stdout.write(self.style.ERROR("Fix ad groups first!"))
                        return

                    current_modifier = float(elm["source_cpc"] / elm["cpc"])
                else:
                    if elm["cpm"] is None:
                        self.stdout.write(self.style.ERROR("Fix ad groups first!"))
                        return

                    current_modifier = float(elm["source_cpm"] / elm["cpm"])

                if elm["modifier"] is None:
                    create_list.append(
                        {
                            "ad_group_id": elm["id"],
                            "type": bid_modifiers.BidModifierType.SOURCE,
                            "target": elm["source_id"],
                            "modifier": current_modifier,
                        }
                    )
                elif abs(current_modifier - elm["modifier"]) > 1e-8:
                    update_list.append({"id": elm["modifier_id"], "modifier": current_modifier})

            if update_list:
                if fix:
                    updated_count = models.BidModifier.objects.filter(id__in=set(e["id"] for e in update_list)).update(
                        modifier=Case(*[When(id=e["id"], then=e["modifier"]) for e in update_list])
                    )
                    update_count += updated_count
                else:
                    update_count += len(update_list)

            if create_list:
                create_count += len(create_list)
                if fix:
                    bid_modifier_list = [models.BidModifier(**e) for e in create_list]
                    models.BidModifier.objects.bulk_create(bid_modifier_list)

        if update_count > 0:
            if fix:
                self.stdout.write(self.style.SUCCESS("Fixed {} source bid modifiers!".format(update_count)))
            else:
                self.stdout.write(
                    self.style.WARNING("Found {} source bid modifiers that need to be fixed.".format(update_count))
                )

        else:
            self.stdout.write(self.style.SUCCESS("No source bid modifiers need to be fixed!"))

        if create_count > 0:
            if fix:
                self.stdout.write(self.style.SUCCESS("Created {} source bid modifiers!".format(create_count)))
            else:
                self.stdout.write(
                    self.style.WARNING("Found {} source bid modifiers that need to be created.".format(create_count))
                )

        else:
            self.stdout.write(self.style.SUCCESS("No source bid modifiers need to be created!"))


def _to_local_currency(value, exchange_rate):
    return value.quantize(Decimal("10") ** value.as_tuple().exponent) * exchange_rate
