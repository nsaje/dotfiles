import math
from decimal import Decimal

from django.db.models import Max
from django.db.models import Q

from core.features import bid_modifiers
from dash import constants
from dash import models
from utils.command_helpers import Z1Command

BATCH_SIZE = 10000


class Command(Z1Command):
    help = "Verify changes done by source bid modifier migrations"

    def handle(self, *args, **options):
        faulty_ad_group_ids = self.verify_no_empty_bid_values()
        if faulty_ad_group_ids:
            self.stdout.write(self.style.ERROR("Empty bid values in AdGroups: {}".format(faulty_ad_group_ids)))
            return
        else:
            self.stdout.write("Empty bid values validation OK.")

        faulty_ad_group_ids = self.verify_bid_values()
        if faulty_ad_group_ids:
            self.stdout.write(self.style.ERROR("Faulty bid values in AdGroups: {}".format(faulty_ad_group_ids)))
            return
        else:
            self.stdout.write("Faulty bid values validation OK.")

        faulty_ad_group_ids = self.verify_no_max_bid_values()
        if faulty_ad_group_ids:
            self.stdout.write(
                self.style.ERROR("Faulty bid values in AdGroups with no max bid values: {}".format(faulty_ad_group_ids))
            )
            return
        else:
            self.stdout.write("Faulty bid values in AdGroups with no max bid values validation OK.")

        faulty_ad_group_ids = self.verify_bid_modifiers()
        if faulty_ad_group_ids:
            self.stdout.write(self.style.ERROR("Faulty bid modifiers in AdGroups: {}".format(faulty_ad_group_ids)))
            return
        else:
            self.stdout.write("Faulty bid modifiers in AdGroups validation OK.")

        self.stdout.write(self.style.SUCCESS("No faults found!"))

    def verify_no_empty_bid_values(self):
        faulty_ad_group_ids = set(
            models.AdGroup.objects.filter(
                Q(settings__cpc=None)
                | Q(settings__cpm=None)
                | Q(settings__local_cpc=None)
                | Q(settings__local_cpm=None)
            ).values_list("id", flat=True)
        )

        return faulty_ad_group_ids

    def verify_bid_values(self):
        faulty_ad_group_ids = set()

        ad_group_qs = models.AdGroup.objects.exclude(Q(settings__cpc_cc=None) | Q(settings__max_cpm=None))
        for ag in ad_group_qs.iterator(chunk_size=BATCH_SIZE):
            if (
                (ag.settings.cpc_cc != ag.settings.cpc)
                | (ag.settings.local_cpc_cc != ag.settings.local_cpc)
                | (ag.settings.max_cpm != ag.settings.cpm)
                | (ag.settings.local_max_cpm != ag.settings.local_cpm)
            ):
                faulty_ad_group_ids.add(ag.id)

        return faulty_ad_group_ids

    def verify_no_max_bid_values(self):
        faulty_ad_group_ids = set()

        ad_group_qs = models.AdGroup.objects.filter(Q(settings__cpc_cc=None) | Q(settings__max_cpm=None))

        goal_map = {}
        for cgv in (
            models.CampaignGoalValue.objects.filter(
                campaign_goal__campaign__id__in=ad_group_qs.filter(bidding_type=constants.BiddingType.CPC).values_list(
                    "campaign__id", flat=True
                ),
                campaign_goal__type=constants.CampaignGoalKPI.CPC,
            )
            .order_by("campaign_goal__campaign__id", "-created_dt")
            .distinct("campaign_goal__campaign__id")
            .values("value", "campaign_goal__campaign__id")
        ):
            goal_map[cgv["campaign_goal__campaign__id"]] = cgv["value"]

        ad_group_qs = ad_group_qs.values(
            "id",
            "bidding_type",
            "campaign__id",
            "settings__cpc_cc",
            "settings__local_cpc_cc",
            "settings__cpc",
            "settings__local_cpc",
            "settings__max_cpm",
            "settings__local_max_cpm",
            "settings__cpm",
            "settings__local_cpm",
            max_cpc_cc=Max("adgroupsource__settings__cpc_cc"),
            max_local_cpc_cc=Max("adgroupsource__settings__local_cpc_cc"),
            max_cpm=Max("adgroupsource__settings__cpm"),
            max_local_cpm=Max("adgroupsource__settings__local_cpm"),
        )
        for ag in ad_group_qs.iterator(chunk_size=BATCH_SIZE):
            if ag["settings__cpc_cc"] is None:
                if _wrong_settings_value(
                    ag["settings__cpc"], ag["settings__local_cpc"], ag["max_cpc_cc"], ag["max_local_cpc_cc"]
                ):
                    faulty_ad_group_ids.add(ag["id"])
                if ag["bidding_type"] == constants.BiddingType.CPC:
                    if ag["campaign__id"] in goal_map:
                        if ag["settings__cpc"] < round(goal_map[ag["campaign__id"]], 4):
                            faulty_ad_group_ids.add(ag["id"])
            else:
                if (ag["settings__cpc_cc"] != ag["settings__cpc"]) | (
                    ag["settings__local_cpc_cc"] != ag["settings__local_cpc"]
                ):
                    faulty_ad_group_ids.add(ag["id"])

            if ag["settings__max_cpm"] is None:
                if _wrong_settings_value(
                    ag["settings__cpm"], ag["settings__local_cpm"], ag["max_cpm"], ag["max_local_cpm"]
                ):
                    faulty_ad_group_ids.add(ag["id"])
            else:
                if (ag["settings__max_cpm"] != ag["settings__cpm"]) | (
                    ag["settings__local_max_cpm"] != ag["settings__local_cpm"]
                ):
                    faulty_ad_group_ids.add(ag["id"])

        return faulty_ad_group_ids

    def verify_bid_modifiers(self):
        faulty_ad_group_ids = set()

        bm_map = {
            (e["ad_group__id"], e["target"]): e["modifier"]
            for e in models.BidModifier.objects.filter(type=bid_modifiers.BidModifierType.SOURCE)
            .values("ad_group__id", "target", "modifier")
            .iterator(chunk_size=BATCH_SIZE)
        }

        ad_group_qs = models.AdGroup.objects.values(
            "id",
            "bidding_type",
            "settings__cpc",
            "settings__cpm",
            "adgroupsource__source__id",
            "adgroupsource__settings__cpc_cc",
            "adgroupsource__settings__cpm",
            "adgroupsource__settings__state",
        )

        for ag in ad_group_qs.iterator(chunk_size=BATCH_SIZE):
            if ag["adgroupsource__source__id"] is None:
                continue

            modifier = bm_map.get((ag["id"], str(ag["adgroupsource__source__id"])))
            if modifier is None:
                if ag["adgroupsource__settings__state"] == constants.AdGroupSourceSettingsState.ACTIVE:
                    faulty_ad_group_ids.add(ag["id"])
                continue

            if ag["bidding_type"] == constants.BiddingType.CPC:
                if _modifier_not_ok(modifier, ag["adgroupsource__settings__cpc_cc"], ag["settings__cpc"]):
                    faulty_ad_group_ids.add(ag["id"])
            else:
                if _modifier_not_ok(modifier, ag["adgroupsource__settings__cpm"], ag["settings__cpm"]):
                    faulty_ad_group_ids.add(ag["id"])

        return faulty_ad_group_ids


def _wrong_settings_value(val, local_val, max_val, max_local_val):
    if (_round_smaller(val, max_val) if max_val is not None else False) | (
        _round_smaller(local_val, max_local_val) if max_local_val is not None else False
    ):
        return True

    return False


def _round_smaller(val_1, val_2, round=4):
    if val_1 - val_2 < -Decimal(math.pow(10, -round)):
        return True

    return False


def _modifier_not_ok(modifier, ad_group_source_value, ad_group_value):
    return abs(modifier - float(Decimal(ad_group_source_value) / Decimal(ad_group_value))) > 1e-7
