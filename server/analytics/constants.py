from utils.constant_base import ConstantBase


class CampaignDeliveryStatus(ConstantBase):
    OK = "ok"
    IAB_UNDEFINED = "iab-undefined"
    MISSING_POSTCLICK_STATS = "missing-postclick-stats"
    MISSING_POSTCLICK_SETUP = "missing-postclick-setup"
    NO_ACTIVE_AD_GROUPS = "no-active-ad-groups"
    CAMPAIGN_WITH_ENDING_BUDGET = "campaign-with-ending-budget"
    CPA_NO_CONVERSIONS = "CPA-goal-with-no-conversions"

    _VALUES = {
        OK: "OK",
        IAB_UNDEFINED: "IAB Category undefined",
        MISSING_POSTCLICK_STATS: "Missing engagement data",
        MISSING_POSTCLICK_SETUP: "Google / Adobe analytics are not set up",
        NO_ACTIVE_AD_GROUPS: "Campaign has budget but no active ad groups",
        CAMPAIGN_WITH_ENDING_BUDGET: "Campaign with budget ending within 30 days",
        CPA_NO_CONVERSIONS: "Campaign set with CPA goal but has no conversions",
    }


class AdGroupDeliveryStatus(ConstantBase):
    OK = "ok"
    MISSING_ADS = "missing-ads"
    NO_ADS_APPROVED = "no-ads-approved"
    NO_ACTIVE_SOURCES = "no-active-sources"
    RTB_AS_1_NO_SOURCES = "rtb-as-1-no-sources"
    WHITELIST_AND_INTERESTS = "whitelist-and-interest-targeting"
    WHITELIST_AND_DATA = "whitelist-and-data-targeting"
    TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING = "too-little-b1-sources-for-interest-targeting"
    NO_ACTIVE_ADS = "no-active-ads"
    INTEREST_TARGETING_AND_BLUEKAI = "interest-targeting-and-Bluekai"

    _VALUES = {
        OK: "OK",
        MISSING_ADS: "Missing content ads",
        NO_ADS_APPROVED: "No ads approved on any media source",
        NO_ACTIVE_SOURCES: "No active sources on a running ad group",
        RTB_AS_1_NO_SOURCES: "RTB-as-1 enabled but no active b1 sources",
        WHITELIST_AND_INTERESTS: "Whitelist and interest targeting set",
        WHITELIST_AND_DATA: "Whitelist and data targeting set",
        TOO_LITTLE_B1_SOURCES_FOR_INTEREST_TARGETING: "Too little active b1 sources for successfull interest targeting",
        NO_ACTIVE_ADS: "No active content ads on a running ad group",
        INTEREST_TARGETING_AND_BLUEKAI: "Interest targeting and Blukai set at the same time",
    }
