from utils.constant_base import ConstantBase


class CampaignDeliveryStatus(ConstantBase):
    OK = "ok"
    NO_GOAL = "no-goal"
    IAB_UNDEFINED = "iab-undefined"
    NO_BUDGET = "no-budget"
    MISSING_POSTCLICK_STATS = "missing-postclick-stats"
    MISSING_POSTCLICK_SETUP = "missing-postclick-setup"
    LOW_PACING = "low-pacing"
    HIGH_PACING = "high-pacing"
    NO_ACTIVE_AD_GROUPS = "no-active-ad-groups"

    _VALUES = {
        OK: "OK",
        NO_GOAL: "No campaign goal set",
        IAB_UNDEFINED: "IAB Category undefined",
        NO_BUDGET: "No budget",
        MISSING_POSTCLICK_STATS: "Missing engagement data",
        MISSING_POSTCLICK_SETUP: "Google / Adobe analytics are not set up",
        LOW_PACING: "Campaign pacing is low",
        HIGH_PACING: "Campaign pacing is high",
        NO_ACTIVE_AD_GROUPS: "Campaign has budget but no active ad groups",
    }


class AdGroupDeliveryStatus(ConstantBase):
    OK = "ok"
    MISSING_ADS = "missing-ads"
    NO_ADS_APPROVED = "no-ads-approved"
    NO_ACTIVE_SOURCES = "no-active-sources"
    RTB_AS_1_NO_SOURCES = "rtb-as-1-no-sources"
    WHITELIST_AND_INTERESTS = "whitelist-and-interest-targeting"
    WHITELIST_AND_DATA = "whitelist-and-data-targeting"
    MISSING_DATA_COST = "missing-data-cost"
    TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING = "too-little-b1-sources-for-interest-targeting"
    MISSING_VIDEO_COST = "missing-video-cost"

    _VALUES = {
        OK: "OK",
        MISSING_ADS: "Missing content ads",
        NO_ADS_APPROVED: "No ads approved on any media source",
        NO_ACTIVE_SOURCES: "No active sources on a running ad group",
        RTB_AS_1_NO_SOURCES: "RTB-as-1 enabled but no active b1 sources",
        WHITELIST_AND_INTERESTS: "Whitelist and interest targeting set",
        WHITELIST_AND_DATA: "Whitelist and data targeting set",
        MISSING_DATA_COST: "Missing data cost",
        MISSING_VIDEO_COST: "Missing video cost",
        TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING: "Too little active b1 sources for successfull interest targeting",
    }
