# -*- coding: utf-8 -*-

from dash import regions
from utils.constant_base import ConstantBase

MAX_CONVERSION_GOALS_PER_CAMPAIGN = 15

GA_PROPERTY_ID_REGEX = r"UA-([0-9]+)-([0-9]+)"
DEFAULT_CALL_TO_ACTION = "Read more"


class AdGroupSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {ACTIVE: "Enabled", INACTIVE: "Paused"}


class AdGroupRunningStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {ACTIVE: "Active", INACTIVE: "Paused"}


class AdGroupSettingsAutopilotState(ConstantBase):
    ACTIVE_CPC_BUDGET = 1
    INACTIVE = 2
    ACTIVE_CPC = 3
    ACTIVE = 4

    _VALUES = {
        ACTIVE_CPC: "Optimize Bids",
        ACTIVE_CPC_BUDGET: "Optimize Bids and Daily Spend Caps",
        ACTIVE: "Optimal Bid Bidding Strategy",
        INACTIVE: "Disabled",  # TODO: RTAP: Change this after all agencies are migrated
    }


class B1AutopilotState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {ACTIVE: "Active", INACTIVE: "Inactive"}


class AdGroupSourceSettingsState(ConstantBase):
    # keep in sync with zwei
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {ACTIVE: "Enabled", INACTIVE: "Paused"}


class BiddingType(ConstantBase):
    CPC = 1
    CPM = 2

    _VALUES = {CPC: "CPC", CPM: "CPM"}


class BillingType(ConstantBase):
    DEFAULT = 1
    FIXED_CPM = 2
    FIXED_CPC = 3
    _VALUES = {DEFAULT: "default", FIXED_CPC: "fixed CPC", FIXED_CPM: "fixed CPM"}


class ExportStatus(ConstantBase):
    # Generalized constant used for export output formatting. It handles conversion to text for various state classes.
    ACTIVE = 1
    INACTIVE = 2
    ARCHIVED = 3

    _VALUES = {ACTIVE: "Active", INACTIVE: "Inactive", ARCHIVED: "Archived"}


class AdTargetDevice(ConstantBase):
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"

    _VALUES = {DESKTOP: "Desktop", TABLET: "Tablet", MOBILE: "Mobile"}


class AdTargetEnvironment(ConstantBase):
    APP = "app"
    SITE = "site"

    _VALUES = {APP: "In-app", SITE: "Website"}


class AdTargetLocation(ConstantBase):
    _VALUES = dict(
        list(regions.COUNTRY_BY_CODE.items())
        + list(regions.DMA_BY_CODE.items())
        + list(regions.SUBDIVISION_BY_CODE.items())
    )

    @classmethod
    def get_choices(cls):
        return list(cls._VALUES.items())


class ContentAdSubmissionStatus(ConstantBase):
    NOT_SUBMITTED = -1
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    LIMIT_REACHED = 4
    NOT_AVAILABLE = 5

    _VALUES = {
        NOT_SUBMITTED: "Not submitted",
        PENDING: "Pending",
        APPROVED: "Approved",
        REJECTED: "Rejected",
        LIMIT_REACHED: "Limit reached",
        NOT_AVAILABLE: "Not available",
    }


class ContentAdSspdStatus(ConstantBase):
    # NOTE: in sync with ContentAdSubmissionStatus

    PENDING = 1
    APPROVED = 2
    BLOCKED = 3

    _VALUES = {PENDING: "Pending", APPROVED: "Approved", BLOCKED: "Blocked"}


class ContentAdSourceState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {ACTIVE: "Enabled", INACTIVE: "Paused"}


class TrackerMethod(ConstantBase):
    IMG = "img"
    JS = "js"

    _VALUES = {IMG: "Image-pixel tracking", JS: "Javascript-based tracking"}


class TrackerEventType(ConstantBase):
    IMPRESSION = "impression"
    VIEWABILITY = "viewability"

    _VALUES = {IMPRESSION: "Impression", VIEWABILITY: "Viewability"}


class TrackerPrivacyFramework(ConstantBase):
    GDPR = "gdpr"
    CCPA = "ccpa"

    _VALUES = {GDPR: "GDPR", CCPA: "CCPA"}


class AdType(ConstantBase):
    CONTENT = 1
    VIDEO = 2
    IMAGE = 3
    AD_TAG = 4

    _VALUES = {CONTENT: "Content ad", VIDEO: "Video ad", IMAGE: "Image display ad", AD_TAG: "Display ad tag"}


class DisplayAdSize(ConstantBase):
    INLINE_RECTANGLE = (300, 250)  # width, height
    MOBILE_LEADERBOARD = (320, 50)
    LEADERBOARD = (728, 90)
    LARGE_RECTANGLE = (336, 280)
    HALF_PAGE = (300, 600)
    WIDESKYSCRAPER = (120, 600)
    LARGE_MOBILE_BANNER = (320, 100)
    BANNER = (468, 60)
    PORTRAIT = (300, 1050)
    LARGE_LEADERBOARD = (970, 90)
    BILLBOARD = (970, 250)
    SQUARE = (250, 250)
    SMALL_SQUARE = (200, 200)
    SMALL_RECTANGLE = (180, 150)
    BUTTON = (125, 125)

    _VALUES = {
        INLINE_RECTANGLE: "Inline rectangle",
        MOBILE_LEADERBOARD: "Mobile leaderboard",
        LEADERBOARD: "Leaderboard",
        LARGE_RECTANGLE: "Large rectangle",
        HALF_PAGE: "Half page",
        WIDESKYSCRAPER: "Wideskyscraper",
        WIDESKYSCRAPER: "Wideskyscraper",
        LARGE_MOBILE_BANNER: "Large mobile banner",
        BANNER: "Banner",
        PORTRAIT: "Portrait",
        LARGE_LEADERBOARD: "Large leaderboard",
        BILLBOARD: "Billboard",
        SQUARE: "Square",
        SMALL_SQUARE: "Small square",
        SMALL_RECTANGLE: "Small rectangle",
        BUTTON: "Button",
    }


class PublisherStatus(ConstantBase):
    ENABLED = 1
    BLACKLISTED = 2
    PENDING = 3

    _VALUES = {ENABLED: "Active", BLACKLISTED: "Blacklisted", PENDING: "Pending"}


class AccountType(ConstantBase):
    UNKNOWN = 1
    TEST = 2
    SANDBOX = 3
    PILOT = 4
    ACTIVATED = 5
    MANAGED = 6
    PAAS = 7

    _VALUES = {
        UNKNOWN: "Unknown",
        TEST: "Test",
        SANDBOX: "Sandbox",
        PILOT: "Pilot",
        ACTIVATED: "Activated",
        MANAGED: "Managed",
        PAAS: "PAAS",
    }


class CampaignType(ConstantBase):
    CONTENT = 1
    VIDEO = 2
    CONVERSION = 3
    MOBILE = 4
    DISPLAY = 5

    _VALUES = {
        CONTENT: "Native Ad Campaign",
        VIDEO: "Native Video Advertising",
        CONVERSION: "Native Conversion Marketing",
        MOBILE: "Native Mobile App Advertising",
        DISPLAY: "Display Ad Campaign",
    }


class Language(ConstantBase):
    ENGLISH = "en"
    GERMAN = "de"
    GREEK = "el"
    ARABIC = "ar"
    SPANISH = "es"
    FRENCH = "fr"
    INDONESIAN = "id"
    ITALIAN = "it"
    JAPANESE = "ja"
    MALAY = "ms"
    DUTCH = "nl"
    PORTUGUESE = "pt"
    ROMANIAN = "ro"
    RUSSIAN = "ru"
    SWEDISH = "sv"
    TURKISH = "tr"
    VIETNAMESE = "vi"
    SIMPLIFIED_CHINESE = "zh_CN"
    TRADITIONAL_CHINESE = "zh_TW"
    OTHER = "any"

    _VALUES = {
        ARABIC: "Arabic",
        GERMAN: "German",
        GREEK: "Greek",
        ENGLISH: "English",
        SPANISH: "Spanish",
        FRENCH: "French",
        INDONESIAN: "Indonesian",
        ITALIAN: "Italian",
        JAPANESE: "Japanese",
        MALAY: "Malay",
        DUTCH: "Dutch",
        PORTUGUESE: "Portuguese",
        ROMANIAN: "Romanian",
        RUSSIAN: "Russian",
        SWEDISH: "Swedish",
        TURKISH: "Turkish",
        VIETNAMESE: "Vietnamese",
        SIMPLIFIED_CHINESE: "Simplified Chinese",
        TRADITIONAL_CHINESE: "Traditional Chinese",
        OTHER: "Other",
    }


class Currency(ConstantBase):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    AUD = "AUD"
    SGD = "SGD"
    BRL = "BRL"
    MYR = "MYR"
    CHF = "CHF"
    ZAR = "ZAR"
    ILS = "ILS"
    INR = "INR"
    JPY = "JPY"
    CAD = "CAD"
    NZD = "NZD"
    TRY = "TRY"
    MXN = "MXN"

    _VALUES = {
        USD: "US Dollar",
        EUR: "Euro",
        GBP: "British Pound",
        AUD: "Australian Dollar",
        SGD: "Singapore Dollar",
        BRL: "Brazilian Real",
        MYR: "Malaysian Ringgit",
        CHF: "Swiss Franc",
        ZAR: "South African Rand",
        ILS: "Israeli New Shekel",
        INR: "Indian Rupee",
        JPY: "Japanese Yen",
        CAD: "Canadian Dollar",
        NZD: "New Zealand Dollar",
        TRY: "Turkish Lira",
        MXN: "Mexican Peso",
    }


class InfoboxLevel(ConstantBase):
    ADGROUP = "adgroup"
    CAMPAIGN = "campaign"
    ACCOUNT = "account"
    ALL_ACCOUNTS = "all-accounts"

    _VALUES = {ADGROUP: "Ad Group", CAMPAIGN: "Campaign", ACCOUNT: "Account", ALL_ACCOUNTS: "All Accounts"}


class PublisherBlacklistLevel(ConstantBase):

    ADGROUP = "adgroup"
    CAMPAIGN = "campaign"
    ACCOUNT = "account"
    GLOBAL = "global"

    _INT_MAP = {ADGROUP: 1, CAMPAIGN: 2, ACCOUNT: 3, GLOBAL: 4}

    _VALUES = {ADGROUP: "Ad group", CAMPAIGN: "Campaign", ACCOUNT: "Account", GLOBAL: "Global"}

    @classmethod
    def verbose(cls, level, status):
        level_verbose = ""
        if status == PublisherTargetingStatus.BLACKLISTED:
            level_verbose = "Blacklisted in this ad group"
            if level == PublisherBlacklistLevel.CAMPAIGN:
                level_verbose = "Blacklisted in this campaign"
            elif level == PublisherBlacklistLevel.ACCOUNT:
                level_verbose = "Blacklisted in this account"
            elif level == PublisherBlacklistLevel.GLOBAL:
                level_verbose = "Blacklisted globally"
        elif status == PublisherTargetingStatus.WHITELISTED:
            level_verbose = "Whitelisted in this ad group"
            if level == PublisherBlacklistLevel.CAMPAIGN:
                level_verbose = "Whitelisted in this campaign"
            elif level == PublisherBlacklistLevel.ACCOUNT:
                level_verbose = "Whitelisted in this account"
        return level_verbose

    @classmethod
    def compare(cls, level, other):
        mapping = cls._INT_MAP
        return mapping[level].__cmp__(mapping[other])


class PublisherBlacklistFilter(ConstantBase):
    SHOW_ALL = "all"
    SHOW_ACTIVE = "active"
    SHOW_BLACKLISTED = "blacklisted"
    SHOW_WHITELISTED = "whitelisted"

    _VALUES = {SHOW_ALL: "All", SHOW_ACTIVE: "Active", SHOW_BLACKLISTED: "Blacklisted", SHOW_WHITELISTED: "Whitelisted"}


class IABCategory(ConstantBase):
    IAB1 = "IAB1"
    IAB1_1 = "IAB1-1"
    IAB1_2 = "IAB1-2"
    IAB1_3 = "IAB1-3"
    IAB1_4 = "IAB1-4"
    IAB1_5 = "IAB1-5"
    IAB1_6 = "IAB1-6"
    IAB1_7 = "IAB1-7"
    IAB2 = "IAB2"
    IAB2_1 = "IAB2-1"
    IAB2_2 = "IAB2-2"
    IAB2_3 = "IAB2-3"
    IAB2_4 = "IAB2-4"
    IAB2_5 = "IAB2-5"
    IAB2_6 = "IAB2-6"
    IAB2_7 = "IAB2-7"
    IAB2_8 = "IAB2-8"
    IAB2_9 = "IAB2-9"
    IAB2_10 = "IAB2-10"
    IAB2_11 = "IAB2-11"
    IAB2_12 = "IAB2-12"
    IAB2_13 = "IAB2-13"
    IAB2_14 = "IAB2-14"
    IAB2_15 = "IAB2-15"
    IAB2_16 = "IAB2-16"
    IAB2_17 = "IAB2-17"
    IAB2_18 = "IAB2-18"
    IAB2_19 = "IAB2-19"
    IAB2_20 = "IAB2-20"
    IAB2_21 = "IAB2-21"
    IAB2_22 = "IAB2-22"
    IAB2_23 = "IAB2-23"
    IAB3 = "IAB3"
    IAB3_1 = "IAB3-1"
    IAB3_2 = "IAB3-2"
    IAB3_3 = "IAB3-3"
    IAB3_4 = "IAB3-4"
    IAB3_5 = "IAB3-5"
    IAB3_6 = "IAB3-6"
    IAB3_7 = "IAB3-7"
    IAB3_8 = "IAB3-8"
    IAB3_9 = "IAB3-9"
    IAB3_10 = "IAB3-10"
    IAB3_11 = "IAB3-11"
    IAB3_12 = "IAB3-12"
    IAB4 = "IAB4"
    IAB4_1 = "IAB4-1"
    IAB4_2 = "IAB4-2"
    IAB4_3 = "IAB4-3"
    IAB4_4 = "IAB4-4"
    IAB4_5 = "IAB4-5"
    IAB4_6 = "IAB4-6"
    IAB4_7 = "IAB4-7"
    IAB4_8 = "IAB4-8"
    IAB4_9 = "IAB4-9"
    IAB4_10 = "IAB4-10"
    IAB4_11 = "IAB4-11"
    IAB5 = "IAB5"
    IAB5_1 = "IAB5-1"
    IAB5_2 = "IAB5-2"
    IAB5_3 = "IAB5-3"
    IAB5_4 = "IAB5-4"
    IAB5_5 = "IAB5-5"
    IAB5_6 = "IAB5-6"
    IAB5_7 = "IAB5-7"
    IAB5_8 = "IAB5-8"
    IAB5_9 = "IAB5-9"
    IAB5_10 = "IAB5-10"
    IAB5_11 = "IAB5-11"
    IAB5_12 = "IAB5-12"
    IAB5_13 = "IAB5-13"
    IAB5_14 = "IAB5-14"
    IAB5_15 = "IAB5-15"
    IAB6 = "IAB6"
    IAB6_1 = "IAB6-1"
    IAB6_2 = "IAB6-2"
    IAB6_3 = "IAB6-3"
    IAB6_4 = "IAB6-4"
    IAB6_5 = "IAB6-5"
    IAB6_6 = "IAB6-6"
    IAB6_7 = "IAB6-7"
    IAB6_8 = "IAB6-8"
    IAB6_9 = "IAB6-9"
    IAB7 = "IAB7"
    IAB7_1 = "IAB7-1"
    IAB7_2 = "IAB7-2"
    IAB7_3 = "IAB7-3"
    IAB7_4 = "IAB7-4"
    IAB7_5 = "IAB7-5"
    IAB7_6 = "IAB7-6"
    IAB7_7 = "IAB7-7"
    IAB7_8 = "IAB7-8"
    IAB7_9 = "IAB7-9"
    IAB7_10 = "IAB7-10"
    IAB7_11 = "IAB7-11"
    IAB7_12 = "IAB7-12"
    IAB7_13 = "IAB7-13"
    IAB7_14 = "IAB7-14"
    IAB7_15 = "IAB7-15"
    IAB7_16 = "IAB7-16"
    IAB7_17 = "IAB7-17"
    IAB7_18 = "IAB7-18"
    IAB7_19 = "IAB7-19"
    IAB7_20 = "IAB7-20"
    IAB7_21 = "IAB7-21"
    IAB7_22 = "IAB7-22"
    IAB7_23 = "IAB7-23"
    IAB7_24 = "IAB7-24"
    IAB7_25 = "IAB7-25"
    IAB7_26 = "IAB7-26"
    IAB7_27 = "IAB7-27"
    IAB7_28 = "IAB7-28"
    IAB7_29 = "IAB7-29"
    IAB7_30 = "IAB7-30"
    IAB7_31 = "IAB7-31"
    IAB7_32 = "IAB7-32"
    IAB7_33 = "IAB7-33"
    IAB7_34 = "IAB7-34"
    IAB7_35 = "IAB7-35"
    IAB7_36 = "IAB7-36"
    IAB7_37 = "IAB7-37"
    IAB7_38 = "IAB7-38"
    IAB7_39 = "IAB7-39"
    IAB7_40 = "IAB7-40"
    IAB7_41 = "IAB7-41"
    IAB7_42 = "IAB7-42"
    IAB7_43 = "IAB7-43"
    IAB7_44 = "IAB7-44"
    IAB7_45 = "IAB7-45"
    IAB8 = "IAB8"
    IAB8_1 = "IAB8-1"
    IAB8_2 = "IAB8-2"
    IAB8_3 = "IAB8-3"
    IAB8_4 = "IAB8-4"
    IAB8_5 = "IAB8-5"
    IAB8_6 = "IAB8-6"
    IAB8_7 = "IAB8-7"
    IAB8_8 = "IAB8-8"
    IAB8_9 = "IAB8-9"
    IAB8_10 = "IAB8-10"
    IAB8_11 = "IAB8-11"
    IAB8_12 = "IAB8-12"
    IAB8_13 = "IAB8-13"
    IAB8_14 = "IAB8-14"
    IAB8_15 = "IAB8-15"
    IAB8_16 = "IAB8-16"
    IAB8_17 = "IAB8-17"
    IAB8_18 = "IAB8-18"
    IAB9 = "IAB9"
    IAB9_1 = "IAB9-1"
    IAB9_2 = "IAB9-2"
    IAB9_3 = "IAB9-3"
    IAB9_4 = "IAB9-4"
    IAB9_5 = "IAB9-5"
    IAB9_6 = "IAB9-6"
    IAB9_7 = "IAB9-7"
    IAB9_8 = "IAB9-8"
    IAB9_9 = "IAB9-9"
    IAB9_10 = "IAB9-10"
    IAB9_11 = "IAB9-11"
    IAB9_12 = "IAB9-12"
    IAB9_13 = "IAB9-13"
    IAB9_14 = "IAB9-14"
    IAB9_15 = "IAB9-15"
    IAB9_16 = "IAB9-16"
    IAB9_17 = "IAB9-17"
    IAB9_18 = "IAB9-18"
    IAB9_19 = "IAB9-19"
    IAB9_20 = "IAB9-20"
    IAB9_21 = "IAB9-21"
    IAB9_22 = "IAB9-22"
    IAB9_23 = "IAB9-23"
    IAB9_24 = "IAB9-24"
    IAB9_25 = "IAB9-25"
    IAB9_26 = "IAB9-26"
    IAB9_27 = "IAB9-27"
    IAB9_28 = "IAB9-28"
    IAB9_29 = "IAB9-29"
    IAB9_30 = "IAB9-30"
    IAB9_31 = "IAB9-31"
    IAB10 = "IAB10"
    IAB10_1 = "IAB10-1"
    IAB10_2 = "IAB10-2"
    IAB10_3 = "IAB10-3"
    IAB10_4 = "IAB10-4"
    IAB10_5 = "IAB10-5"
    IAB10_6 = "IAB10-6"
    IAB10_7 = "IAB10-7"
    IAB10_8 = "IAB10-8"
    IAB10_9 = "IAB10-9"
    IAB11 = "IAB11"
    IAB11_1 = "IAB11-1"
    IAB11_2 = "IAB11-2"
    IAB11_3 = "IAB11-3"
    IAB11_4 = "IAB11-4"
    IAB11_5 = "IAB11-5"
    IAB12 = "IAB12"
    IAB12_1 = "IAB12-1"
    IAB12_2 = "IAB12-2"
    IAB12_3 = "IAB12-3"
    IAB13 = "IAB13"
    IAB13_1 = "IAB13-1"
    IAB13_2 = "IAB13-2"
    IAB13_3 = "IAB13-3"
    IAB13_4 = "IAB13-4"
    IAB13_5 = "IAB13-5"
    IAB13_6 = "IAB13-6"
    IAB13_7 = "IAB13-7"
    IAB13_8 = "IAB13-8"
    IAB13_9 = "IAB13-9"
    IAB13_10 = "IAB13-10"
    IAB13_11 = "IAB13-11"
    IAB13_12 = "IAB13-12"
    IAB14 = "IAB14"
    IAB14_1 = "IAB14-1"
    IAB14_2 = "IAB14-2"
    IAB14_3 = "IAB14-3"
    IAB14_4 = "IAB14-4"
    IAB14_5 = "IAB14-5"
    IAB14_6 = "IAB14-6"
    IAB14_7 = "IAB14-7"
    IAB14_8 = "IAB14-8"
    IAB15 = "IAB15"
    IAB15_1 = "IAB15-1"
    IAB15_2 = "IAB15-2"
    IAB15_3 = "IAB15-3"
    IAB15_4 = "IAB15-4"
    IAB15_5 = "IAB15-5"
    IAB15_6 = "IAB15-6"
    IAB15_7 = "IAB15-7"
    IAB15_8 = "IAB15-8"
    IAB15_9 = "IAB15-9"
    IAB15_10 = "IAB15-10"
    IAB16 = "IAB16"
    IAB16_1 = "IAB16-1"
    IAB16_2 = "IAB16-2"
    IAB16_3 = "IAB16-3"
    IAB16_4 = "IAB16-4"
    IAB16_5 = "IAB16-5"
    IAB16_6 = "IAB16-6"
    IAB16_7 = "IAB16-7"
    IAB17 = "IAB17"
    IAB17_1 = "IAB17-1"
    IAB17_2 = "IAB17-2"
    IAB17_3 = "IAB17-3"
    IAB17_4 = "IAB17-4"
    IAB17_5 = "IAB17-5"
    IAB17_6 = "IAB17-6"
    IAB17_7 = "IAB17-7"
    IAB17_8 = "IAB17-8"
    IAB17_9 = "IAB17-9"
    IAB17_10 = "IAB17-10"
    IAB17_11 = "IAB17-11"
    IAB17_12 = "IAB17-12"
    IAB17_13 = "IAB17-13"
    IAB17_14 = "IAB17-14"
    IAB17_15 = "IAB17-15"
    IAB17_16 = "IAB17-16"
    IAB17_17 = "IAB17-17"
    IAB17_18 = "IAB17-18"
    IAB17_19 = "IAB17-19"
    IAB17_20 = "IAB17-20"
    IAB17_21 = "IAB17-21"
    IAB17_22 = "IAB17-22"
    IAB17_23 = "IAB17-23"
    IAB17_24 = "IAB17-24"
    IAB17_25 = "IAB17-25"
    IAB17_26 = "IAB17-26"
    IAB17_27 = "IAB17-27"
    IAB17_28 = "IAB17-28"
    IAB17_29 = "IAB17-29"
    IAB17_30 = "IAB17-30"
    IAB17_31 = "IAB17-31"
    IAB17_32 = "IAB17-32"
    IAB17_33 = "IAB17-33"
    IAB17_34 = "IAB17-34"
    IAB17_35 = "IAB17-35"
    IAB17_36 = "IAB17-36"
    IAB17_37 = "IAB17-37"
    IAB17_38 = "IAB17-38"
    IAB17_39 = "IAB17-39"
    IAB17_40 = "IAB17-40"
    IAB17_41 = "IAB17-41"
    IAB17_42 = "IAB17-42"
    IAB17_43 = "IAB17-43"
    IAB17_44 = "IAB17-44"
    IAB18 = "IAB18"
    IAB18_1 = "IAB18-1"
    IAB18_2 = "IAB18-2"
    IAB18_3 = "IAB18-3"
    IAB18_4 = "IAB18-4"
    IAB18_5 = "IAB18-5"
    IAB18_6 = "IAB18-6"
    IAB19 = "IAB19"
    IAB19_1 = "IAB19-1"
    IAB19_2 = "IAB19-2"
    IAB19_3 = "IAB19-3"
    IAB19_4 = "IAB19-4"
    IAB19_5 = "IAB19-5"
    IAB19_6 = "IAB19-6"
    IAB19_7 = "IAB19-7"
    IAB19_8 = "IAB19-8"
    IAB19_9 = "IAB19-9"
    IAB19_10 = "IAB19-10"
    IAB19_11 = "IAB19-11"
    IAB19_12 = "IAB19-12"
    IAB19_13 = "IAB19-13"
    IAB19_14 = "IAB19-14"
    IAB19_15 = "IAB19-15"
    IAB19_16 = "IAB19-16"
    IAB19_17 = "IAB19-17"
    IAB19_18 = "IAB19-18"
    IAB19_19 = "IAB19-19"
    IAB19_20 = "IAB19-20"
    IAB19_21 = "IAB19-21"
    IAB19_22 = "IAB19-22"
    IAB19_23 = "IAB19-23"
    IAB19_24 = "IAB19-24"
    IAB19_25 = "IAB19-25"
    IAB19_26 = "IAB19-26"
    IAB19_27 = "IAB19-27"
    IAB19_28 = "IAB19-28"
    IAB19_29 = "IAB19-29"
    IAB19_30 = "IAB19-30"
    IAB19_31 = "IAB19-31"
    IAB19_32 = "IAB19-32"
    IAB19_33 = "IAB19-33"
    IAB19_34 = "IAB19-34"
    IAB19_35 = "IAB19-35"
    IAB19_36 = "IAB19-36"
    IAB20 = "IAB20"
    IAB20_1 = "IAB20-1"
    IAB20_2 = "IAB20-2"
    IAB20_3 = "IAB20-3"
    IAB20_4 = "IAB20-4"
    IAB20_5 = "IAB20-5"
    IAB20_6 = "IAB20-6"
    IAB20_7 = "IAB20-7"
    IAB20_8 = "IAB20-8"
    IAB20_9 = "IAB20-9"
    IAB20_10 = "IAB20-10"
    IAB20_11 = "IAB20-11"
    IAB20_12 = "IAB20-12"
    IAB20_13 = "IAB20-13"
    IAB20_14 = "IAB20-14"
    IAB20_15 = "IAB20-15"
    IAB20_16 = "IAB20-16"
    IAB20_17 = "IAB20-17"
    IAB20_18 = "IAB20-18"
    IAB20_19 = "IAB20-19"
    IAB20_20 = "IAB20-20"
    IAB20_21 = "IAB20-21"
    IAB20_22 = "IAB20-22"
    IAB20_23 = "IAB20-23"
    IAB20_24 = "IAB20-24"
    IAB20_25 = "IAB20-25"
    IAB20_26 = "IAB20-26"
    IAB20_27 = "IAB20-27"
    IAB21 = "IAB21"
    IAB21_1 = "IAB21-1"
    IAB21_2 = "IAB21-2"
    IAB21_3 = "IAB21-3"
    IAB22 = "IAB22"
    IAB22_1 = "IAB22-1"
    IAB22_2 = "IAB22-2"
    IAB22_3 = "IAB22-3"
    IAB22_4 = "IAB22-4"
    IAB23 = "IAB23"
    IAB23_1 = "IAB23-1"
    IAB23_2 = "IAB23-2"
    IAB23_3 = "IAB23-3"
    IAB23_4 = "IAB23-4"
    IAB23_5 = "IAB23-5"
    IAB23_6 = "IAB23-6"
    IAB23_7 = "IAB23-7"
    IAB23_8 = "IAB23-8"
    IAB23_9 = "IAB23-9"
    IAB23_10 = "IAB23-10"
    IAB24 = "IAB24"
    IAB25 = "IAB25"
    IAB25_1 = "IAB25-1"
    IAB25_2 = "IAB25-2"
    IAB25_3 = "IAB25-3"
    IAB25_4 = "IAB25-4"
    IAB25_5 = "IAB25-5"
    IAB25_6 = "IAB25-6"
    IAB25_7 = "IAB25-7"
    IAB26 = "IAB26"
    IAB26_1 = "IAB26-1"
    IAB26_2 = "IAB26-2"
    IAB26_3 = "IAB26-3"
    IAB26_4 = "IAB26-4"

    _VALUES = {
        IAB1: "Arts & Entertainment",
        IAB1_1: "Books & Literature",
        IAB1_2: "Celebrity Fan/Gossip",
        IAB1_3: "Fine Art",
        IAB1_4: "Humor",
        IAB1_5: "Movies",
        IAB1_6: "Music",
        IAB1_7: "Television",
        IAB2: "Automotive",
        IAB2_1: "Auto Parts",
        IAB2_2: "Auto Repair",
        IAB2_3: "Buying/Selling Cars",
        IAB2_4: "Car Culture",
        IAB2_5: "Certified Pre-Owned",
        IAB2_6: "Convertible",
        IAB2_7: "Coupe",
        IAB2_8: "Crossover",
        IAB2_9: "Diesel",
        IAB2_10: "Electric Vehicle",
        IAB2_11: "Hatchback",
        IAB2_12: "Hybrid",
        IAB2_13: "Luxury",
        IAB2_14: "MiniVan",
        IAB2_15: "Mororcycles",
        IAB2_16: "Off-Road Vehicles",
        IAB2_17: "Performance Vehicles",
        IAB2_18: "Pickup",
        IAB2_19: "Road-Side Assistance",
        IAB2_20: "Sedan",
        IAB2_21: "Trucks & Accessories",
        IAB2_22: "Vintage Cars",
        IAB2_23: "Wagon",
        IAB3: "Business",
        IAB3_1: "Advertising",
        IAB3_2: "Agriculture",
        IAB3_3: "Biotech/Biomedical",
        IAB3_4: "Business Software",
        IAB3_5: "Construction",
        IAB3_6: "Forestry",
        IAB3_7: "Government",
        IAB3_8: "Green Solutions",
        IAB3_9: "Human Resources",
        IAB3_10: "Logistics",
        IAB3_11: "Marketing",
        IAB3_12: "Metals",
        IAB4: "Careers",
        IAB4_1: "Career Planning",
        IAB4_2: "College",
        IAB4_3: "Financial Aid",
        IAB4_4: "Job Fairs",
        IAB4_5: "Job Search",
        IAB4_6: "Resume Writing/Advice",
        IAB4_7: "Nursing",
        IAB4_8: "Scholarships",
        IAB4_9: "Telecommuting",
        IAB4_10: "U.S. Military",
        IAB4_11: "Career Advice",
        IAB5: "Education",
        IAB5_1: "7-12 Education",
        IAB5_2: "Adult Education",
        IAB5_3: "Art History",
        IAB5_4: "College Administration",
        IAB5_5: "College Life",
        IAB5_6: "Distance Learning",
        IAB5_7: "English as a 2nd Language",
        IAB5_8: "Language Learning",
        IAB5_9: "Graduate School",
        IAB5_10: "Homeschooling",
        IAB5_11: "Homework/Study Tips",
        IAB5_12: "K-6 Educators",
        IAB5_13: "Private School",
        IAB5_14: "Special Education",
        IAB5_15: "Studying Business",
        IAB6: "Family & Parenting",
        IAB6_1: "Adoption",
        IAB6_2: "Babies & Toddlers",
        IAB6_3: "Daycare/Pre School",
        IAB6_4: "Family Internet",
        IAB6_5: "Parenting - K-6 Kids",
        IAB6_6: "Parenting teens",
        IAB6_7: "Pregnancy",
        IAB6_8: "Special Needs Kids",
        IAB6_9: "Eldercare",
        IAB7: "Health & Fitness",
        IAB7_1: "Exercise",
        IAB7_2: "A.D.D.",
        IAB7_3: "AIDS/HIV",
        IAB7_4: "Allergies",
        IAB7_5: "Alternative Medicine",
        IAB7_6: "Arthritis",
        IAB7_7: "Asthma",
        IAB7_8: "Autism/PDD",
        IAB7_9: "Bipolar Disorder",
        IAB7_10: "Brain Tumor",
        IAB7_11: "Cancer",
        IAB7_12: "Cholesterol",
        IAB7_13: "Chronic Fatigue Syndrome",
        IAB7_14: "Chronic Pain",
        IAB7_15: "Cold & Flu",
        IAB7_16: "Deafness",
        IAB7_17: "Dental Care",
        IAB7_18: "Depression",
        IAB7_19: "Dermatology",
        IAB7_20: "Diabetes",
        IAB7_21: "Epilepsy",
        IAB7_22: "GERD/Acid Reflux",
        IAB7_23: "Headaches/Migraines",
        IAB7_24: "Heart Disease",
        IAB7_25: "Herbs for Health",
        IAB7_26: "Holistic Healing",
        IAB7_27: "IBS/Crohn's Disease",
        IAB7_28: "Incest/Abuse Support",
        IAB7_29: "Incontinence",
        IAB7_30: "Infertility",
        IAB7_31: "Men's Health",
        IAB7_32: "Nutrition",
        IAB7_33: "Orthopedics",
        IAB7_34: "Panic/Anxiety Disorders",
        IAB7_35: "Pediatrics",
        IAB7_36: "Physical Therapy",
        IAB7_37: "Psychology/Psychiatry",
        IAB7_38: "Senior Health",
        IAB7_39: "Sexuality",
        IAB7_40: "Sleep Disorders",
        IAB7_41: "Smoking Cessation",
        IAB7_42: "Substance Abuse",
        IAB7_43: "Thyroid Disease",
        IAB7_44: "Weight Loss",
        IAB7_45: "Women's Health",
        IAB8: "Food & Drink",
        IAB8_1: "American Cuisine",
        IAB8_2: "Barbecues & Grilling",
        IAB8_3: "Cajun/Creole",
        IAB8_4: "Chinese Cuisine",
        IAB8_5: "Cocktails/Beer",
        IAB8_6: "Coffee/Tea",
        IAB8_7: "Cuisine-Specific",
        IAB8_8: "Desserts & Baking",
        IAB8_9: "Dining Out",
        IAB8_10: "Food Allergies",
        IAB8_11: "French Cuisine",
        IAB8_12: "Health/Lowfat Cooking",
        IAB8_13: "Italian Cuisine",
        IAB8_14: "Japanese Cuisine",
        IAB8_15: "Mexican Cuisine",
        IAB8_16: "Vegan",
        IAB8_17: "Vegetarian",
        IAB8_18: "Wine",
        IAB9: "Hobbies & Interests",
        IAB9_1: "Art/Technology",
        IAB9_2: "Arts & Crafts",
        IAB9_3: "Beadwork",
        IAB9_4: "Birdwatching",
        IAB9_5: "Board Games/Puzzles",
        IAB9_6: "Candle & Soap Making",
        IAB9_7: "Card Games",
        IAB9_8: "Chess",
        IAB9_9: "Cigars",
        IAB9_10: "Collecting",
        IAB9_11: "Comic Books",
        IAB9_12: "Drawing/Sketching",
        IAB9_13: "Freelance Writing",
        IAB9_14: "Genealogy",
        IAB9_15: "Getting Published",
        IAB9_16: "Guitar",
        IAB9_17: "Home Recording",
        IAB9_18: "Investors & Patents",
        IAB9_19: "Jewelry Making",
        IAB9_20: "Magic & Illusion",
        IAB9_21: "Needlework",
        IAB9_22: "Painting",
        IAB9_23: "Photography",
        IAB9_24: "Radio",
        IAB9_25: "Roleplaying Games",
        IAB9_26: "Sci-Fi & Fantasy",
        IAB9_27: "Scrapbooking",
        IAB9_28: "Screenwriting",
        IAB9_29: "Stamps & Coins",
        IAB9_30: "Video & Computer Games",
        IAB9_31: "Woodworking",
        IAB10: "Home & Garden",
        IAB10_1: "Appliances",
        IAB10_2: "Entertaining",
        IAB10_3: "Environmental Safety",
        IAB10_4: "Gardening",
        IAB10_5: "Home Repair",
        IAB10_6: "Home Theater",
        IAB10_7: "Interior Decorating",
        IAB10_8: "Landscaping",
        IAB10_9: "Remodeling & Construction",
        IAB11: "Law, Gov't & Politics",
        IAB11_1: "Immigration",
        IAB11_2: "Legal Issues",
        IAB11_3: "U.S. Government Resources",
        IAB11_4: "Politics",
        IAB11_5: "Commentary",
        IAB12: "News",
        IAB12_1: "International News",
        IAB12_2: "National News",
        IAB12_3: "Local News",
        IAB13: "Personal Finance",
        IAB13_1: "Beginning Investing",
        IAB13_2: "Credit/Debt & Loans",
        IAB13_3: "Financial News",
        IAB13_4: "Financial Planning",
        IAB13_5: "Hedge Fund",
        IAB13_6: "Insurance",
        IAB13_7: "Investing",
        IAB13_8: "Mutual Funds",
        IAB13_9: "Options",
        IAB13_10: "Retirement Planning",
        IAB13_11: "Stocks",
        IAB13_12: "Tax Planning",
        IAB14: "Society",
        IAB14_1: "Dating",
        IAB14_2: "Divorce Support",
        IAB14_3: "Gay Life",
        IAB14_4: "Marriage",
        IAB14_5: "Senior Living",
        IAB14_6: "Teens",
        IAB14_7: "Weddings",
        IAB14_8: "Ethnic Specific",
        IAB15: "Science",
        IAB15_1: "Astrology",
        IAB15_2: "Biology",
        IAB15_3: "Chemistry",
        IAB15_4: "Geology",
        IAB15_5: "Paranormal Phenomena",
        IAB15_6: "Physics",
        IAB15_7: "Space/Astronomy",
        IAB15_8: "Geography",
        IAB15_9: "Botany",
        IAB15_10: "Weather",
        IAB16: "Pets",
        IAB16_1: "Aquariums",
        IAB16_2: "Birds",
        IAB16_3: "Cats",
        IAB16_4: "Dogs",
        IAB16_5: "Large Animals",
        IAB16_6: "Reptiles",
        IAB16_7: "Veterinary Medicine",
        IAB17: "Sports",
        IAB17_1: "Auto Racing",
        IAB17_2: "Baseball",
        IAB17_3: "Bicycling",
        IAB17_4: "Bodybuilding",
        IAB17_5: "Boxing",
        IAB17_6: "Canoeing/Kayaking",
        IAB17_7: "Cheerleading",
        IAB17_8: "Climbing",
        IAB17_9: "Cricket",
        IAB17_10: "Figure Skating",
        IAB17_11: "Fly Fishing",
        IAB17_12: "Football",
        IAB17_13: "Freshwater Fishing",
        IAB17_14: "Game & Fish",
        IAB17_15: "Golf",
        IAB17_16: "Horse Racing",
        IAB17_17: "Horses",
        IAB17_18: "Hunting/Shooting",
        IAB17_19: "Inline Skating",
        IAB17_20: "Martial Arts",
        IAB17_21: "Mountain Biking",
        IAB17_22: "NASCAR Racing",
        IAB17_23: "Olympics",
        IAB17_24: "Paintball",
        IAB17_25: "Power & Motorcycles",
        IAB17_26: "Pro Basketball",
        IAB17_27: "Pro Ice Hockey",
        IAB17_28: "Rodeo",
        IAB17_29: "Rugby",
        IAB17_30: "Running/Jogging",
        IAB17_31: "Sailing",
        IAB17_32: "Saltwater Fishing",
        IAB17_33: "Scuba Diving",
        IAB17_34: "Skateboarding",
        IAB17_35: "Skiing",
        IAB17_36: "Snowboarding",
        IAB17_37: "Surfing/Bodyboarding",
        IAB17_38: "Swimming",
        IAB17_39: "Table Tennis/Ping-Pong",
        IAB17_40: "Tennis",
        IAB17_41: "Volleyball",
        IAB17_42: "Walking",
        IAB17_43: "Waterski/Wakeboard",
        IAB17_44: "World Soccer",
        IAB18: "Style & Fashion",
        IAB18_1: "Beauty",
        IAB18_2: "Body Art",
        IAB18_3: "Fashion",
        IAB18_4: "Jewelry",
        IAB18_5: "Clothing",
        IAB18_6: "Accessories",
        IAB19: "Technology & Computing",
        IAB19_1: "3-D Graphics",
        IAB19_2: "Animation",
        IAB19_3: "Antivirus Software",
        IAB19_4: "C/C++",
        IAB19_5: "Cameras & Camcorders",
        IAB19_6: "Cell Phones",
        IAB19_7: "Computer Certification",
        IAB19_8: "Computer Networking",
        IAB19_9: "Computer Peripherals",
        IAB19_10: "Computer Reviews",
        IAB19_11: "Data Centers",
        IAB19_12: "Databases",
        IAB19_13: "Desktop Publishing",
        IAB19_14: "Desktop Video",
        IAB19_15: "Email",
        IAB19_16: "Graphics Software",
        IAB19_17: "Home Video/DVD",
        IAB19_18: "Internet Technology",
        IAB19_19: "Java",
        IAB19_20: "JavaScript",
        IAB19_21: "Mac Support",
        IAB19_22: "MP3/MIDI",
        IAB19_23: "Net Conferencing",
        IAB19_24: "Net for Beginners",
        IAB19_25: "Network Security",
        IAB19_26: "Palmtops/PDAs",
        IAB19_27: "PC Support",
        IAB19_28: "Portable",
        IAB19_29: "Entertainment",
        IAB19_30: "Shareware/Freeware",
        IAB19_31: "Unix",
        IAB19_32: "Visual Basic",
        IAB19_33: "Web Clip Art",
        IAB19_34: "Web Design/HTML",
        IAB19_35: "Web Search",
        IAB19_36: "Windows",
        IAB20: "Travel",
        IAB20_1: "Adventure Travel",
        IAB20_2: "Africa",
        IAB20_3: "Air Travel",
        IAB20_4: "Australia & New Zealand",
        IAB20_5: "Bed & Breakfasts",
        IAB20_6: "Budget Travel",
        IAB20_7: "Business Travel",
        IAB20_8: "By US Locale",
        IAB20_9: "Camping",
        IAB20_10: "Canada",
        IAB20_11: "Caribbean",
        IAB20_12: "Cruises",
        IAB20_13: "Eastern Europe",
        IAB20_14: "Europe",
        IAB20_15: "France",
        IAB20_16: "Greece",
        IAB20_17: "Honeymoons/Getaways",
        IAB20_18: "Hotels",
        IAB20_19: "Italy",
        IAB20_20: "Japan",
        IAB20_21: "Mexico & Central America",
        IAB20_22: "National Parks",
        IAB20_23: "South America",
        IAB20_24: "Spas",
        IAB20_25: "Theme Parks",
        IAB20_26: "Traveling with Kids",
        IAB20_27: "United Kingdom",
        IAB21: "Real Estate",
        IAB21_1: "Apartments",
        IAB21_2: "Architects",
        IAB21_3: "Buying/Selling Homes",
        IAB22: "Shopping",
        IAB22_1: "Contests & Freebies",
        IAB22_2: "Couponing",
        IAB22_3: "Comparison",
        IAB22_4: "Engines",
        IAB23: "Religion & Spirituality",
        IAB23_1: "Alternative Religions",
        IAB23_2: "Atheism/Agnosticism",
        IAB23_3: "Buddhism",
        IAB23_4: "Catholicism",
        IAB23_5: "Christianity",
        IAB23_6: "Hinduism",
        IAB23_7: "Islam",
        IAB23_8: "Judaism",
        IAB23_9: "Latter-Day Saints",
        IAB23_10: "Pagan/Wiccan",
        IAB24: "Uncategorized",
        IAB25: "Non-Standard Content",
        IAB25_1: "Unmoderated UGC",
        IAB25_2: "Extreme Graphic/Explicit Violence",
        IAB25_3: "Pornography",
        IAB25_4: "Profane Content",
        IAB25_5: "Hate Content",
        IAB25_6: "Under Construction",
        IAB25_7: "Incentivized",
        IAB26: "Illegal Content",
        IAB26_1: "Illegal Content",
        IAB26_2: "Warez",
        IAB26_3: "Spyware/Malware",
        IAB26_4: "Copyright Infringement",
    }


IAB_CATEGORY_DEFAULT_ICON_MAP = {
    "IAB1": "d/icons/IAB1",
    "IAB2": "d/icons/IAB2",
    "IAB3": "d/icons/IAB3",
    "IAB4": "d/icons/IAB4",
    "IAB5": "d/icons/IAB5",
    "IAB6": "d/icons/IAB6",
    "IAB7": "d/icons/IAB7",
    "IAB8": "d/icons/IAB8",
    "IAB9": "d/icons/IAB9",
    "IAB10": "d/icons/IAB10",
    "IAB11": "d/icons/IAB11",
    "IAB12": "d/icons/IAB12",
    "IAB13": "d/icons/IAB13",
    "IAB14": "d/icons/IAB14",
    "IAB15": "d/icons/IAB15",
    "IAB16": "d/icons/IAB16",
    "IAB17": "d/icons/IAB17",
    "IAB18": "d/icons/IAB18",
    "IAB19": "d/icons/IAB19",
    "IAB20": "d/icons/IAB20",
    "IAB21": "d/icons/IAB21",
    "IAB22": "d/icons/IAB22",
    "IAB23": "d/icons/IAB23",
    "IAB24": "d/icons/IAB24",
    "IAB25": "d/icons/IAB25",
    "IAB26": "d/icons/IAB26",
}


class InterestCategory(ConstantBase):
    ENTERTAINMENT = "entertainment"
    FUN_QUIZZES = "fun_quizzes"
    MUSIC = "music"
    CARS = "cars"
    FINANCE = "finance"
    EDUCATION = "education"
    FAMILY = "family"
    HEALTH = "health"
    FOOD = "food"
    HOBBIES = "hobbies"
    GAMES = "games"
    HOME = "home"
    POLITICS_LAW = "politics_law"
    MEDIA = "media"
    DATING = "dating"
    SCIENCE = "science"
    WEATHER = "weather"
    PETS = "pets"
    SPORTS = "sports"
    FASHION = "fashion"
    TECHNOLOGY = "technology"
    UTILITY = "utility"
    TRAVEL = "travel"
    SHOPPING_COUPONS = "shopping_coupons"
    RELIGION = "religion"
    COMMUNICATION = "communication"
    CAREER = "career"
    PREMIUM = "premium"
    WOMEN = "women"
    MEN = "men"

    # internal from here on
    FOREIGN = "foreign"
    FRENCH = "french"
    SPANISH = "spanish"
    OTHER = "other"
    UNKNOWN = "?"
    OUTBRAIN = "outbrain"
    # this is a cisco specific thing and is set on the bidder based on page url keywords
    TECHNOLOGY_CONTEXTUAL = "technology-contextual"
    FUN = "fun"
    QUIZZES = "quizzes"
    POLITICS = "politics"
    LAW = "law"
    COUPONS = "coupons"
    SHOPPING = "shopping"

    _VALUES = {
        ENTERTAINMENT: "Arts & Entertainment",
        FUN_QUIZZES: "Viral, lists & Quizzes",
        MUSIC: "Music",
        CARS: "Automotive",
        FINANCE: "Business & Finance",
        EDUCATION: "Education",
        FAMILY: "Family & Parenting",
        HEALTH: "Health & Fitness",
        FOOD: "Food & Drink",
        HOBBIES: "Hobbies & Interests",
        GAMES: "Games & Gaming",
        HOME: "Home & Garden",
        POLITICS_LAW: "Law, Gov’t & Politics",
        MEDIA: "News",
        DATING: "Dating & Relationships",
        SCIENCE: "Science",
        WEATHER: "Weather & Environment",
        PETS: "Pets",
        SPORTS: "Sports",
        FASHION: "Beauty & Fashion",
        TECHNOLOGY: "Technology",
        UTILITY: "Apps & Online services",
        TRAVEL: "Travel",
        SHOPPING_COUPONS: "Shopping",
        RELIGION: "Religion & Spirituality",
        COMMUNICATION: "Communication Tools",
        CAREER: "Careers",
        PREMIUM: "Premium",
        WOMEN: "Women’s Lifestyle",
        MEN: "Men’s Lifestyle",
        FOREIGN: "Foreign",
        FRENCH: "French",
        SPANISH: "Spanish",
        OTHER: "Other",
        UNKNOWN: "Unknown",
        OUTBRAIN: "Outbrain",
        TECHNOLOGY_CONTEXTUAL: "Technology - Contextual",
        FUN: "Fun & Entertaining Sites",
        QUIZZES: "Quizzes",
        POLITICS: "Gov’t & Politics",
        LAW: "Law",
        COUPONS: "Couponing",
        SHOPPING: "Shopping",
    }


class PromotionGoal(ConstantBase):
    BRAND_BUILDING = 1
    TRAFFIC_ACQUISITION = 2
    CONVERSIONS = 3

    _VALUES = {BRAND_BUILDING: "Brand Building", TRAFFIC_ACQUISITION: "Traffic Acquisition", CONVERSIONS: "Conversions"}


class CampaignGoal(ConstantBase):
    CPA = 1
    PERCENT_BOUNCE_RATE = 2
    NEW_UNIQUE_VISITORS = 3
    SECONDS_TIME_ON_SITE = 4
    PAGES_PER_SESSION = 5

    _VALUES = {
        CPA: "CPA",
        PERCENT_BOUNCE_RATE: "% bounce rate",
        NEW_UNIQUE_VISITORS: "new unique visitors",
        SECONDS_TIME_ON_SITE: "seconds time on site",
        PAGES_PER_SESSION: "pages per session",
    }


class CampaignGoalKPI(ConstantBase):
    TIME_ON_SITE = 1
    MAX_BOUNCE_RATE = 2
    PAGES_PER_SESSION = 3
    CPA = 4
    CPC = 5
    #    CPM = 6
    NEW_UNIQUE_VISITORS = 7
    CPV = 8
    CP_NON_BOUNCED_VISIT = 9
    CP_NEW_VISITOR = 10
    CP_PAGE_VIEW = 11
    CPCV = 12

    _VALUES = {
        TIME_ON_SITE: "Time on Site - Seconds",
        MAX_BOUNCE_RATE: "Max Bounce Rate",
        PAGES_PER_SESSION: "Pageviews per Visit",
        CPA: "$CPA",
        CPC: "CPC",
        #        CPM: '$CPM',
        NEW_UNIQUE_VISITORS: "New Unique Visitors",
        CPV: "Cost per Visit",
        CP_NON_BOUNCED_VISIT: "Cost per Non-Bounced Visit",
        CP_NEW_VISITOR: "Cost per New Visitor",
        CP_PAGE_VIEW: "Cost per Pageview",
        CPCV: "Cost per Completed Video View",
    }


class CampaignGoalPerformance(ConstantBase):
    UNDERPERFORMING = 1
    AVERAGE = 2
    SUPERPERFORMING = 3

    _VALUES = {UNDERPERFORMING: "Underperforming", AVERAGE: "Average performance", SUPERPERFORMING: "Superperforming"}


class Emoticon(ConstantBase):
    HAPPY = 1
    NEUTRAL = 2
    SAD = 3

    _VALUES = {HAPPY: "Happy", SAD: "Sad", NEUTRAL: "Neutral"}


class SourceAction(ConstantBase):
    CAN_UPDATE_STATE = 1
    CAN_UPDATE_CPC = 2
    CAN_UPDATE_DAILY_BUDGET_AUTOMATIC = 3
    CAN_MANAGE_CONTENT_ADS = 4
    HAS_3RD_PARTY_DASHBOARD = 5
    CAN_MODIFY_START_DATE = 6
    CAN_MODIFY_END_DATE = 7
    CAN_MODIFY_DEVICE_TARGETING = 8
    # CAN_MODIFY_TRACKING_CODES = 9
    CAN_MODIFY_AD_GROUP_NAME = 10
    CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC = 11
    UPDATE_TRACKING_CODES_ON_CONTENT_ADS = 12
    CAN_UPDATE_DAILY_BUDGET_MANUAL = 13
    CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL = 14
    CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC = 15
    CAN_MODIFY_COUNTRY_TARGETING = 16
    CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL = 17
    CAN_FETCH_REPORT_BY_PUBLISHER = 18
    CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC = 19

    _VALUES = {
        CAN_UPDATE_STATE: "Can update state",
        CAN_UPDATE_CPC: "Can update CPC",
        CAN_UPDATE_DAILY_BUDGET_AUTOMATIC: "Can update daily budget automatically",
        CAN_MANAGE_CONTENT_ADS: "Can manage content ads",
        HAS_3RD_PARTY_DASHBOARD: "Has 3rd party dashboard",
        CAN_MODIFY_START_DATE: "Can modify start date",
        CAN_MODIFY_END_DATE: "Can modify end date",
        CAN_MODIFY_DEVICE_TARGETING: "Can modify device targeting",
        CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC: "Can modify DMA and subdivision targeting automatically",
        CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL: "Can modify DMA and subdivision targeting manually",
        CAN_MODIFY_COUNTRY_TARGETING: "Can modify targeting by country",
        # CAN_MODIFY_TRACKING_CODES: 'Can modify tracking codes',
        CAN_MODIFY_AD_GROUP_NAME: "Can modify adgroup name",
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC: "Can modify ad group IAB category automatically",
        UPDATE_TRACKING_CODES_ON_CONTENT_ADS: "Update tracking codes on content ads",
        CAN_UPDATE_DAILY_BUDGET_MANUAL: "Can update daily budget manually",
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL: "Can modify ad group IAB category manually",
        CAN_FETCH_REPORT_BY_PUBLISHER: "Can fetch report by publishers",
        CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC: "Can modify publisher blacklist",
    }


class SourceSubmissionType(ConstantBase):
    DEFAULT = 1
    AD_GROUP = 2
    BATCH = 3

    _VALUES = {DEFAULT: "Default", AD_GROUP: "One submission per ad group", BATCH: "Submit whole batch at once"}


class SourceType(ConstantBase):
    ADBLADE = "adblade"
    GRAVITY = "gravity"
    NRELATE = "nrelate"
    OUTBRAIN = "outbrain"
    YAHOO = "yahoo"
    ZEMANTA = "zemanta"
    DISQUS = "disqus"
    B1 = "b1"
    FACEBOOK = "facebook"

    _VALUES = {
        ADBLADE: "AdBlade",
        GRAVITY: "Gravity",
        NRELATE: "nRelate",
        OUTBRAIN: "Outbrain",
        YAHOO: "Yahoo",
        ZEMANTA: "Zemanta",
        B1: "B1",
        FACEBOOK: "Facebook",
    }


class ConversionGoalType(ConstantBase):
    PIXEL = 1
    GA = 2
    OMNITURE = 3

    _VALUES = {PIXEL: "Conversion Pixel", GA: "Google Analytics", OMNITURE: "Adobe Analytics"}


REPORT_GOAL_TYPES = [ConversionGoalType.GA, ConversionGoalType.OMNITURE]
PIXEL_GOAL_TYPE = ConversionGoalType.PIXEL


class UploadBatchStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3
    CANCELLED = 4

    _VALUES = {DONE: "Done", FAILED: "Failed", IN_PROGRESS: "In progress", CANCELLED: "Cancelled"}


class UploadBatchType(ConstantBase):
    INSERT = 1
    EDIT = 2
    CLONE = 3

    _VALUES = {INSERT: "Insert", EDIT: "Edit", CLONE: "Clone"}


class CreativeBatchStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3

    _VALUES = {DONE: "Done", FAILED: "Failed", IN_PROGRESS: "In progress"}


class RegionType(ConstantBase):
    COUNTRY = 1
    SUBDIVISION = 2
    DMA = 3

    _VALUES = {
        COUNTRY: "Country",
        SUBDIVISION: "U.S. state",  # NOTE update when subdivisions other than U.S. states are added
        DMA: "DMA",
    }


class CreditLineItemStatus(ConstantBase):
    SIGNED = 1  # Only adding BudgetLineItems is permitted
    PENDING = 2  # Internal "waiting" status, fields are editable
    CANCELED = 3  # Adding BudgetLineItems is not permitted

    _VALUES = {SIGNED: "Signed", PENDING: "Pending", CANCELED: "Canceled"}


class BudgetLineItemState(ConstantBase):
    ACTIVE = 1
    PENDING = 2
    INACTIVE = 3
    DEPLETED = 4

    _VALUES = {ACTIVE: "Active", PENDING: "Pending", INACTIVE: "Inactive", DEPLETED: "Depleted"}


class ScheduledReportSendingFrequency(ConstantBase):
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3

    _VALUES = {DAILY: "Daily", WEEKLY: "Weekly", MONTHLY: "Monthly"}


class ScheduledReportDayOfWeek(ConstantBase):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    _VALUES = {
        MONDAY: "Monday",
        TUESDAY: "Tuesday",
        WEDNESDAY: "Wednesday",
        THURSDAY: "Thursday",
        FRIDAY: "Friday",
        SATURDAY: "Saturday",
        SUNDAY: "Sunday",
    }


class ScheduledReportTimePeriod(ConstantBase):
    YESTERDAY = 1
    LAST_7_DAYS = 2
    LAST_30_DAYS = 3
    THIS_WEEK = 4
    LAST_WEEK = 5
    THIS_MONTH = 6
    LAST_MONTH = 7

    _VALUES = {
        YESTERDAY: "Yesterday",
        LAST_7_DAYS: "Last 7 Days",
        LAST_30_DAYS: "Last 30 Days",
        THIS_WEEK: "This Week",
        LAST_WEEK: "Last Week",
        THIS_MONTH: "This Month",
        LAST_MONTH: "Last Month",
    }


class ScheduledReportState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2
    REMOVED = 3

    _VALUES = {ACTIVE: "Enabled", INACTIVE: "Paused", REMOVED: "Removed"}


class ScheduledReportGranularity(ConstantBase):
    ALL_ACCOUNTS = 1
    ACCOUNT = 2
    CAMPAIGN = 3
    AD_GROUP = 4
    CONTENT_AD = 5

    _VALUES = {
        ALL_ACCOUNTS: "All Accounts",
        ACCOUNT: "Account",
        CAMPAIGN: "Campaign",
        AD_GROUP: "Ad Group",
        CONTENT_AD: "Content Ad",
    }


class ScheduledReportLevel(ConstantBase):
    ALL_ACCOUNTS = 1
    ACCOUNT = 2
    CAMPAIGN = 3
    AD_GROUP = 4

    _VALUES = {ALL_ACCOUNTS: "All Accounts", ACCOUNT: "Account", CAMPAIGN: "Campaign", AD_GROUP: "Ad Group"}


class ScheduledReportSent(ConstantBase):
    SUCCESS = 1
    FAILED = 2

    _VALUES = {SUCCESS: "Success", FAILED: "Failed"}


class GATrackingType(ConstantBase):
    EMAIL = 1
    API = 2

    _VALUES = {EMAIL: "Email", API: "API"}


class SystemUserType(ConstantBase):
    CAMPAIGN_STOP = 1
    AUTOPILOT = 2
    K1_USER = 3
    RULES = 4

    _VALUES = {
        CAMPAIGN_STOP: "Campaign Stop",
        AUTOPILOT: "Zemanta Autopilot",
        K1_USER: "System User ",
        RULES: "Automation Rules",
    }


class AsyncUploadJobStatus(ConstantBase):
    PENDING_START = 1
    WAITING_RESPONSE = 2
    OK = 3
    FAILED = 4

    _VALUES = {PENDING_START: "Pending", WAITING_RESPONSE: "Waiting for response", OK: "OK", FAILED: "Failed"}


class DeviceType(ConstantBase):
    """
    OpenRTB values:
    --+-----------------
    1 | Mobile/Tablet
    2 | Personal Computer
    3 | Connected TV
    4 | Phone
    5 | Tablet
    6 | Connected Device
    7 | Set Top Box

    """

    UNKNOWN = None
    # MOBILE = 1  # legacy
    DESKTOP = 2
    TV = 3
    MOBILE = 4
    TABLET = 5
    # CONNECTED = 6  # joined with TV
    # SET_TOP_BOX = 7  # joined with TV

    _VALUES = {
        UNKNOWN: "Not reported",
        # MOBILE: 'Mobile',
        DESKTOP: "Desktop",
        TV: "TV & SetTop Box",
        MOBILE: "Mobile",
        TABLET: "Tablet",
        # CONNECTED: 'Connected',
        # SET_TOP_BOX: 'SetTop Box',
    }


class Age(ConstantBase):
    UNDEFINED = None
    AGE_18_20 = "18-20"
    AGE_21_29 = "21-29"
    AGE_30_39 = "30-39"
    AGE_40_49 = "40-49"
    AGE_50_64 = "50-64"
    AGE_65_MORE = "65+"

    _VALUES = {
        UNDEFINED: "Not reported",
        AGE_18_20: "18-20",
        AGE_21_29: "21-29",
        AGE_30_39: "30-39",
        AGE_40_49: "40-49",
        AGE_50_64: "50-64",
        AGE_65_MORE: "65 and older",
    }


class Gender(ConstantBase):
    UNDEFINED = None
    MEN = "male"
    WOMEN = "female"

    _VALUES = {UNDEFINED: "Not reported", MEN: "Men", WOMEN: "Women"}


class AgeGender(ConstantBase):
    UNDEFINED = None
    AGE_18_20_MEN = "18-20 male"
    AGE_18_20_WOMEN = "18-20 female"
    AGE_18_20_UNDEFINED = "18-20 "  # spaces are intentional
    AGE_21_29_MEN = "21-29 male"
    AGE_21_29_WOMEN = "21-29 female"
    AGE_21_29_UNDEFINED = "21-29 "
    AGE_30_39_MEN = "30-39 male"
    AGE_30_39_WOMEN = "30-39 female"
    AGE_30_39_UNDEFINED = "30-39 "
    AGE_40_49_MEN = "40-49 male"
    AGE_40_49_WOMEN = "40-49 female"
    AGE_40_49_UNDEFINED = "40-49 "
    AGE_50_64_MEN = "50-64 male"
    AGE_50_64_WOMEN = "50-64 female"
    AGE_50_64_UNDEFINED = "50-64 "
    AGE_65_MORE_MEN = "65+ male"
    AGE_65_MORE_WOMEN = "65+ female"
    AGE_65_MORE_UNDEFINED = "65+ "

    _VALUES = {
        UNDEFINED: "Not reported",
        AGE_18_20_MEN: "18-20 Men",
        AGE_18_20_WOMEN: "18-20 Women",
        AGE_18_20_UNDEFINED: "18-20 Undefined",
        AGE_21_29_MEN: "21-29 Men",
        AGE_21_29_WOMEN: "21-29 Women",
        AGE_21_29_UNDEFINED: "21-29 Undefined",
        AGE_30_39_MEN: "30-39 Men",
        AGE_30_39_WOMEN: "30-39 Women",
        AGE_30_39_UNDEFINED: "30-39 Undefined",
        AGE_40_49_MEN: "40-49 Men",
        AGE_40_49_WOMEN: "40-49 Women",
        AGE_40_49_UNDEFINED: "40-49 Undefined",
        AGE_50_64_MEN: "50-64 Men",
        AGE_50_64_WOMEN: "50-64 Women",
        AGE_50_64_UNDEFINED: "50-64 Undefined",
        AGE_65_MORE_MEN: "65+ Men",
        AGE_65_MORE_WOMEN: "65+ Women",
        AGE_65_MORE_UNDEFINED: "65+ Undefined",
    }


class ConversionType(ConstantBase):
    CLICK = 1
    VIEW = 2

    _VALUES = {CLICK: "Click-through conversion", VIEW: "View-through conversion"}


class ConversionWindows(ConstantBase):
    LEQ_1_DAY = 24
    LEQ_7_DAYS = 168
    LEQ_30_DAYS = 720

    _VALUES = {LEQ_1_DAY: "1 day", LEQ_7_DAYS: "7 days", LEQ_30_DAYS: "30 days"}


class ConversionWindowsLegacy(ConversionWindows):
    LEQ_1_DAY = 24
    LEQ_7_DAYS = 168
    LEQ_30_DAYS = 720
    LEQ_90_DAYS = 2160

    _VALUES = dict(ConversionWindows._VALUES)
    _VALUES.update({LEQ_90_DAYS: "90 days"})


class ConversionWindowsViewthrough(ConstantBase):
    LEQ_1_DAY = 24

    _VALUES = {LEQ_1_DAY: "1 day"}


class EmailTemplateType(ConstantBase):

    ADGROUP_CHANGE = 1
    CAMPAIGN_CHANGE = 2
    BUDGET_CHANGE = 3
    PIXEL_ADD = 4
    PASSWORD_RESET = 5
    USER_NEW = 6
    SUPPLY_REPORT = 7
    SCHEDULED_EXPORT_REPORT = 8
    BUDGET_DEPLETING = 9
    CAMPAIGN_STOPPED = 10
    AUTOPILOT_AD_GROUP_CHANGE = 11
    AUTOPILOT_AD_GROUP_BUDGET_INIT = 12
    DEMO_RUNNING = 15
    LIVESTREAM_SESSION = 16
    DAILY_MANAGEMENT_REPORT = 17
    OUTBRAIN_ACCOUNTS_RUNNING_OUT = 18  # Deprecated, cannot be removed due to migration
    GA_SETUP_INSTRUCTIONS = 19
    ASYNC_REPORT_RESULTS = 20
    DEPLETING_CREDITS = 21
    ACCOUNT_CHANGE = 22
    WEEKLY_CLIENT_REPORT = 23
    PACING_NOTIFICATION = 24
    WEEKLY_INVENTORY_REPORT = 25  # Deprecated, cannot be removed due to migration
    NEW_DEVICE_LOGIN = 26
    ASYNC_SCHEDULED_REPORT_RESULTS = 27
    OEN_POSTCLICKKPI_CPA_FACTORS = 28
    ASYNC_REPORT_FAIL = 29
    AUTOPILOT_CAMPAIGN_CHANGE = 30
    AUTOPILOT_CAMPAIGN_BUDGET_INIT = 31
    CAMPAIGNSTOP_DEPLETING = 32
    USER_ENABLE_RESTAPI = 33
    CAMPAIGN_CREATED = 34
    AUTOMATION_RULE_RUN = 35
    AUTOMATION_RULE_NO_CHANGES = 36
    AUTOMATION_RULE_ERRORS = 37
    CAMPAIGN_CLONED_SUCCESS = 38
    CAMPAIGN_CLONED_ERROR = 39
    AD_GROUP_CLONED_SUCCESS = 40
    AD_GROUP_CLONED_ERROR = 41
    CREDIT_DEPLETED_80_PERCENT = 42
    CREDIT_DEPLETED_90_PERCENT = 43
    UNKNOWN_SALES_OFFICE = 44

    _VALUES = {
        ADGROUP_CHANGE: "Ad group settings change",
        CAMPAIGN_CHANGE: "Campaign settings change",
        ACCOUNT_CHANGE: "Account settings change",
        BUDGET_CHANGE: "Budget change",
        PIXEL_ADD: "New conversion pixel",
        PASSWORD_RESET: "User password reset",
        USER_NEW: "New user introduction email",
        SUPPLY_REPORT: "Supply report",
        SCHEDULED_EXPORT_REPORT: "Scheduled report",
        BUDGET_DEPLETING: "Depleting budget notification",
        CAMPAIGN_STOPPED: "Campaign stopped notification",
        AUTOPILOT_AD_GROUP_CHANGE: "Autopilot changes notification",
        AUTOPILOT_AD_GROUP_BUDGET_INIT: "Autopilot initialisation notification",
        DEMO_RUNNING: "Demo is running",
        LIVESTREAM_SESSION: "Livestream sesion id",
        DAILY_MANAGEMENT_REPORT: "Daily management report",
        OUTBRAIN_ACCOUNTS_RUNNING_OUT: "Unused Outbrain accounts running out",
        GA_SETUP_INSTRUCTIONS: "Google Analytics Setup Instructions",
        ASYNC_REPORT_RESULTS: "Report results",
        DEPLETING_CREDITS: "Depleting credits",
        WEEKLY_CLIENT_REPORT: "Weekly client report",
        PACING_NOTIFICATION: "Pacing notification",
        WEEKLY_INVENTORY_REPORT: "Weekly inventory report",
        NEW_DEVICE_LOGIN: "New device login",
        ASYNC_SCHEDULED_REPORT_RESULTS: "Scheduled report results",
        OEN_POSTCLICKKPI_CPA_FACTORS: "Zemanta OEN CPA Optimization Factors",
        ASYNC_REPORT_FAIL: "Report fail",
        AUTOPILOT_CAMPAIGN_CHANGE: "Campaign Autopilot changes notification",
        AUTOPILOT_CAMPAIGN_BUDGET_INIT: "Campaign Autopilot initialisation notification",
        CAMPAIGNSTOP_DEPLETING: "Real-time campaign stop budget depleting",
        USER_ENABLE_RESTAPI: "User was granted REST API access",
        CAMPAIGN_CREATED: "Campaign created",
        AUTOMATION_RULE_RUN: "Automation rule run",
        AUTOMATION_RULE_NO_CHANGES: "Automation rule run without changes",
        AUTOMATION_RULE_ERRORS: "Automation rule run with errors",
        CAMPAIGN_CLONED_SUCCESS: "Campaign cloned successfully",
        CAMPAIGN_CLONED_ERROR: "Campaign cloned error",
        AD_GROUP_CLONED_SUCCESS: "Ad group cloned successfully",
        AD_GROUP_CLONED_ERROR: "Ad group cloned error",
        CREDIT_DEPLETED_80_PERCENT: "Credit depleted 80 percent",
        CREDIT_DEPLETED_90_PERCENT: "Credit depleted 90 percent",
        UNKNOWN_SALES_OFFICE: "Externally managed user was created with unknown sales office",
    }


class ImageCrop(ConstantBase):
    CENTER = "center"
    FACES = "faces"
    ENTROPY = "entropy"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

    _VALUES = {
        CENTER: "Center",
        FACES: "Faces",
        ENTROPY: "Entropy",
        LEFT: "Left",
        RIGHT: "Right",
        TOP: "Top",
        BOTTOM: "Bottom",
    }


class HistoryLevel(ConstantBase):
    """The difference between global and agency level is that agency for some users
    is the global level but involves only some accounts. Global spans the entire system.
    Examples are global blacklisting and report scheduling.
    """

    AD_GROUP = 1
    CAMPAIGN = 2
    ACCOUNT = 3
    AGENCY = 4
    GLOBAL = 5

    _VALUES = {
        AD_GROUP: "Ad Group Level",
        CAMPAIGN: "Campaign Level",
        ACCOUNT: "Account Level",
        AGENCY: "Agency Level",
        GLOBAL: "All Accounts",
    }


class HistoryActionType(ConstantBase):
    GOAL_CHANGE = 1
    BUDGET_CHANGE = 2
    CREDIT_CHANGE = 3
    PUBLISHER_BLACKLIST_CHANGE = 4
    GLOBAL_PUBLISHER_BLACKLIST_CHANGE = 5
    REPORTING_MANAGE = 6
    CONTENT_AD_STATE_CHANGE = 7
    SETTINGS_CHANGE = 8
    CREATE = 9
    CONTENT_AD_CREATE = 10
    CONVERSION_PIXEL_CREATE = 11
    CONVERSION_PIXEL_ARCHIVE_RESTORE = 12
    ARCHIVE_RESTORE = 13
    CONTENT_AD_ARCHIVE_RESTORE = 14
    MEDIA_SOURCE_SETTINGS_CHANGE = 15
    MEDIA_SOURCE_ADD = 16
    CONVERSION_PIXEL_RENAME = 17
    AUDIENCE_CREATE = 18
    AUDIENCE_ARCHIVE = 19
    AUDIENCE_RESTORE = 20
    AUDIENCE_UPDATE = 22
    CONVERSION_PIXEL_SET_REDIRECT_URL = 23
    CONVERSION_PIXEL_REMOVE_REDIRECT_URL = 24
    PUBLISHER_GROUP_CREATE = 25
    PUBLISHER_GROUP_UPDATE = 26
    CONTENT_AD_EDIT = 26
    CONVERSION_PIXEL_CREATE_AS_ADDITIONAL = 28
    DEAL_CONNECTION_CREATE = 29
    DEAL_CONNECTION_DELETE = 30
    BID_MODIFIER_UPDATE = 31
    BID_MODIFIER_DELETE = 32
    RULE_RUN = 33

    _VALUES = {
        GOAL_CHANGE: "Change Campaign Goal",
        BUDGET_CHANGE: "Change Budget",
        CREDIT_CHANGE: "Change Credit",
        PUBLISHER_BLACKLIST_CHANGE: "Set Publisher Blacklist",
        GLOBAL_PUBLISHER_BLACKLIST_CHANGE: "Set Global Publisher Blacklist",
        REPORTING_MANAGE: "Manage Reporting",
        CONTENT_AD_STATE_CHANGE: "Set Content Ad(s) State",
        SETTINGS_CHANGE: "Change Settings",
        CREATE: "Create",
        CONTENT_AD_CREATE: "Create Content Ad",
        CONTENT_AD_EDIT: "Edit Content Ad",
        CONVERSION_PIXEL_CREATE: "Create Conversion Pixel",
        CONVERSION_PIXEL_ARCHIVE_RESTORE: "Archive/Restore Conversion Pixel",
        ARCHIVE_RESTORE: "Archive/Restore",
        CONTENT_AD_ARCHIVE_RESTORE: "Archive/Restore Content Ad(s)",
        MEDIA_SOURCE_SETTINGS_CHANGE: "Set Media Source Settings",
        MEDIA_SOURCE_ADD: "Add Media Source",
        CONVERSION_PIXEL_RENAME: "Rename conversion pixel",
        AUDIENCE_CREATE: "Create custom audience",
        AUDIENCE_ARCHIVE: "Archive custom audience",
        AUDIENCE_RESTORE: "Restore custom audience",
        AUDIENCE_UPDATE: "Update custom audience",
        CONVERSION_PIXEL_SET_REDIRECT_URL: "Set redirect url for pixel",
        CONVERSION_PIXEL_REMOVE_REDIRECT_URL: "Remove redirect url for pixel",
        PUBLISHER_GROUP_CREATE: "Create publisher group",
        PUBLISHER_GROUP_UPDATE: "Update publisher group",
        CONVERSION_PIXEL_CREATE_AS_ADDITIONAL: "Create Conversion Pixel as additional audience pixel",
        DEAL_CONNECTION_CREATE: "Create deal connection",
        DEAL_CONNECTION_DELETE: "Delete deal connection",
        BID_MODIFIER_UPDATE: "Update bid modifier",
        BID_MODIFIER_DELETE: "Delete bid modifier",
        RULE_RUN: "Automation rule run",
    }


class SlugType(ConstantBase):
    FACEBOOK = "facebook"

    _VALUES = {FACEBOOK: "Facebook"}


class AudienceRuleType(ConstantBase):
    STARTS_WITH = 1
    CONTAINS = 2
    VISIT = 5

    _VALUES = {STARTS_WITH: "Starts with", CONTAINS: "Contains", VISIT: "Visit"}


class Level(object):
    ALL_ACCOUNTS = "all_accounts"
    ACCOUNTS = "accounts"
    CAMPAIGNS = "campaigns"
    AD_GROUPS = "ad_groups"
    CONTENT_ADS = "content_ads"


class AlertType(ConstantBase):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"

    _VALUES = {INFO: "Info", SUCCESS: "Success", WARNING: "Warning", DANGER: "Danger"}


class CpcConstraintType(ConstantBase):
    MANUAL = 1
    OUTBRAIN_BLACKLIST = 2

    _VALUES = {MANUAL: "Manual", OUTBRAIN_BLACKLIST: "Outbrain blacklist"}


class PublisherTargetingStatus(ConstantBase):
    # a replacement for PublisherStatus

    WHITELISTED = 1
    BLACKLISTED = 2
    UNLISTED = 3

    _VALUES = {WHITELISTED: "Whitelisted", BLACKLISTED: "Blacklisted", UNLISTED: "Active"}


class Service(ConstantBase):
    Z1 = "z1"
    K1 = "k1"
    R1 = "r1"
    B1 = "b1"

    _VALUES = {Z1: "Zemanta One", K1: "Konsistency One", R1: "Redirector", B1: "Bidder"}


class Whitelabel(ConstantBase):
    GREENPARK = "greenpark"
    ADTECHNACITY = "adtechnacity"
    NEWSCORP = "newscorp"
    BURDA = "burda"
    MEDIAMOND = "mediamond"
    ADYOULIKE = "adyoulike"
    DAS = "das"

    _VALUES = {
        GREENPARK: "Green Park Content",
        ADTECHNACITY: "Adtechnacity",
        NEWSCORP: "Newscorp",
        BURDA: "Burda",
        MEDIAMOND: "Mediamond",
        ADYOULIKE: "Adyoulike",
        DAS: "Native Ocean",
    }


class LocationType(ConstantBase):
    COUNTRY = "co"
    REGION = "re"
    CITY = "ci"
    DMA = "dma"
    ZIP = "zip"

    _VALUES = {COUNTRY: "Country", REGION: "State / Region", CITY: "City", DMA: "DMA", ZIP: "Postal Code"}


class OperatingSystem(ConstantBase):
    UNKNOWN = None
    ANDROID = "android"
    IOS = "ios"
    WINPHONE = "winphone"
    WINRT = "winrt"
    WINDOWS = "windows"
    MACOSX = "macosx"
    LINUX = "linux"
    CHROMEOS = "chromeos"

    _VALUES = {
        UNKNOWN: "Not reported",
        ANDROID: "Android",
        IOS: "iOS",
        WINPHONE: "Windows Phone",
        WINRT: "WinRT",
        WINDOWS: "Windows",
        MACOSX: "macOS",
        LINUX: "Linux",
        CHROMEOS: "ChromeOS",
    }


class OperatingSystemVersion(ConstantBase):
    UNKNOWN = None
    ANDROID_2_1 = "android_2_1"
    ANDROID_2_2 = "android_2_2"
    ANDROID_2_3 = "android_2_3"
    ANDROID_3_0 = "android_3_0"
    ANDROID_3_1 = "android_3_1"
    ANDROID_3_2 = "android_3_2"
    ANDROID_4_0 = "android_4_0"
    ANDROID_4_1 = "android_4_1"
    ANDROID_4_2 = "android_4_2"
    ANDROID_4_3 = "android_4_3"
    ANDROID_4_4 = "android_4_4"
    ANDROID_5_0 = "android_5_0"
    ANDROID_5_1 = "android_5_1"
    ANDROID_6_0 = "android_6_0"
    ANDROID_7_0 = "android_7_0"
    ANDROID_7_1 = "android_7_1"
    ANDROID_8_0 = "android_8_0"
    ANDROID_8_1 = "android_8_1"
    ANDROID_9_0 = "android_9_0"
    ANDROID_10_0 = "android_10_0"
    ANDROID_11_0 = "android_11_0"
    IOS_3_2 = "ios_3_2"
    IOS_4_0 = "ios_4_0"
    IOS_4_1 = "ios_4_1"
    IOS_4_2 = "ios_4_2"
    IOS_4_3 = "ios_4_3"
    IOS_5_0 = "ios_5_0"
    IOS_5_1 = "ios_5_1"
    IOS_6_0 = "ios_6_0"
    IOS_6_1 = "ios_6_1"
    IOS_7_0 = "ios_7_0"
    IOS_7_1 = "ios_7_1"
    IOS_8_0 = "ios_8_0"
    IOS_8_1 = "ios_8_1"
    IOS_8_2 = "ios_8_2"
    IOS_8_3 = "ios_8_3"
    IOS_8_4 = "ios_8_4"
    IOS_9_0 = "ios_9_0"
    IOS_9_1 = "ios_9_1"
    IOS_9_2 = "ios_9_2"
    IOS_9_3 = "ios_9_3"
    IOS_10_0 = "ios_10_0"
    IOS_10_1 = "ios_10_1"
    IOS_10_2 = "ios_10_2"
    IOS_10_3 = "ios_10_3"
    IOS_11_0 = "ios_11_0"
    IOS_12_0 = "ios_12_0"
    IOS_12_1 = "ios_12_1"
    IOS_12_2 = "ios_12_2"
    IOS_12_3 = "ios_12_3"
    IOS_12_4 = "ios_12_4"
    IOS_13_0 = "ios_13_0"
    IOS_13_1 = "ios_13_1"
    IOS_13_2 = "ios_13_2"
    IOS_13_3 = "ios_13_3"
    IOS_13_4 = "ios_13_4"
    IOS_13_5 = "ios_13_5"
    IOS_13_6 = "ios_13_6"
    IOS_13_7 = "ios_13_7"
    IOS_14_0 = "ios_14_0"
    WINPHONE_7 = "winphone_7"
    WINPHONE_8_0 = "winphone_8_0"
    WINPHONE_8_1 = "winphone_8_1"
    WINPHONE_10 = "winphone_10"
    WINDOWS_98 = "windows_98"
    WINDOWS_2000 = "windows_2000"
    WINDOWS_XP = "windows_xp"
    WINDOWS_VISTA = "windows_vista"
    WINDOWS_7 = "windows_7"
    WINDOWS_8 = "windows_8"
    WINDOWS_8_1 = "windows_8_1"
    WINDOWS_10 = "windows_10"
    MACOSX_10_4 = "macosx_10_4"
    MACOSX_10_5 = "macosx_10_5"
    MACOSX_10_6 = "macosx_10_6"
    MACOSX_10_7 = "macosx_10_7"
    MACOSX_10_8 = "macosx_10_8"
    MACOSX_10_9 = "macosx_10_9"
    MACOSX_10_10 = "macosx_10_10"
    MACOSX_10_11 = "macosx_10_11"
    MACOSX_10_12 = "macosx_10_12"
    MACOSX_10_13 = "macosx_10_13"
    MACOSX_10_14 = "macosx_10_14"
    MACOSX_10_15 = "macosx_10_15"

    _VALUES = {
        UNKNOWN: "Unknown",
        ANDROID_2_1: "2.1 Eclair",
        ANDROID_2_2: "2.2 Froyo",
        ANDROID_2_3: "2.3 Gingerbread",
        ANDROID_3_0: "3.0 Honeycomb",
        ANDROID_3_1: "3.1 Honeycomb",
        ANDROID_3_2: "3.2 Honeycomb",
        ANDROID_4_0: "4.0 Ice Cream Sandwich",
        ANDROID_4_1: "4.1 Jelly Bean",
        ANDROID_4_2: "4.2 Jelly Bean",
        ANDROID_4_3: "4.3 Jelly Bean",
        ANDROID_4_4: "4.4 KitKat",
        ANDROID_5_0: "5.0 Lollipop",
        ANDROID_5_1: "5.1 Lollipop",
        ANDROID_6_0: "6.0 Marshmallow",
        ANDROID_7_0: "7.0 Nougat",
        ANDROID_7_1: "7.1 Nougat",
        ANDROID_8_0: "8.0 Oreo",
        ANDROID_8_1: "8.1 Oreo",
        ANDROID_9_0: "9.0 Pie",
        ANDROID_10_0: "Android 10",
        ANDROID_11_0: "Android 11",
        IOS_3_2: "3.2",
        IOS_4_0: "4.0",
        IOS_4_1: "4.1",
        IOS_4_2: "4.2",
        IOS_4_3: "4.3",
        IOS_5_0: "5.0",
        IOS_5_1: "5.1",
        IOS_6_0: "6.0",
        IOS_6_1: "6.1",
        IOS_7_0: "7.0",
        IOS_7_1: "7.1",
        IOS_8_0: "8.0",
        IOS_8_1: "8.1",
        IOS_8_2: "8.2",
        IOS_8_3: "8.3",
        IOS_8_4: "8.4",
        IOS_9_0: "9.0",
        IOS_9_1: "9.1",
        IOS_9_2: "9.2",
        IOS_9_3: "9.3",
        IOS_10_0: "10.0",
        IOS_10_1: "10.1",
        IOS_10_2: "10.2",
        IOS_10_3: "10.3",
        IOS_11_0: "11.0",
        IOS_12_0: "12.0",
        IOS_12_1: "12.1",
        IOS_12_2: "12.2",
        IOS_12_3: "12.3",
        IOS_12_4: "12.4",
        IOS_13_0: "13.0",
        IOS_13_1: "13.1",
        IOS_13_2: "13.2",
        IOS_13_3: "13.3",
        IOS_13_4: "13.4",
        IOS_13_5: "13.5",
        IOS_13_6: "13.6",
        IOS_13_7: "13.7",
        IOS_14_0: "14.0",
        WINPHONE_7: "7",
        WINPHONE_8_0: "8.0",
        WINPHONE_8_1: "8.1",
        WINPHONE_10: "10",
        WINDOWS_98: "98",
        WINDOWS_2000: "2000",
        WINDOWS_XP: "XP",
        WINDOWS_VISTA: "Vista",
        WINDOWS_7: "7",
        WINDOWS_8: "8",
        WINDOWS_8_1: "8.1",
        WINDOWS_10: "10",
        MACOSX_10_4: "10.4 Tiger",
        MACOSX_10_5: "10.5 Leopard",
        MACOSX_10_6: "10.6 Snow Leopard",
        MACOSX_10_7: "10.7 Lion",
        MACOSX_10_8: "10.8 Mountain Lion",
        MACOSX_10_9: "10.9 Mavericks",
        MACOSX_10_10: "10.10 Yosemite",
        MACOSX_10_11: "10.11 El Capitan",
        MACOSX_10_12: "10.12 Sierra",
        MACOSX_10_13: "10.13 High Sierra",
        MACOSX_10_14: "10.14 Mojave",
        MACOSX_10_15: "10.15 Catalina",
    }


OSV_MAPPING = {
    # Versions mapped to OS and ordered based on the release date
    OperatingSystem.ANDROID: [
        OperatingSystemVersion.ANDROID_2_1,
        OperatingSystemVersion.ANDROID_2_2,
        OperatingSystemVersion.ANDROID_2_3,
        OperatingSystemVersion.ANDROID_3_0,
        OperatingSystemVersion.ANDROID_3_1,
        OperatingSystemVersion.ANDROID_3_2,
        OperatingSystemVersion.ANDROID_4_0,
        OperatingSystemVersion.ANDROID_4_1,
        OperatingSystemVersion.ANDROID_4_2,
        OperatingSystemVersion.ANDROID_4_3,
        OperatingSystemVersion.ANDROID_4_4,
        OperatingSystemVersion.ANDROID_5_0,
        OperatingSystemVersion.ANDROID_5_1,
        OperatingSystemVersion.ANDROID_6_0,
        OperatingSystemVersion.ANDROID_7_0,
        OperatingSystemVersion.ANDROID_7_1,
        OperatingSystemVersion.ANDROID_8_0,
        OperatingSystemVersion.ANDROID_8_1,
        OperatingSystemVersion.ANDROID_9_0,
        OperatingSystemVersion.ANDROID_10_0,
    ],
    OperatingSystem.IOS: [
        OperatingSystemVersion.IOS_3_2,
        OperatingSystemVersion.IOS_4_0,
        OperatingSystemVersion.IOS_4_1,
        OperatingSystemVersion.IOS_4_2,
        OperatingSystemVersion.IOS_4_3,
        OperatingSystemVersion.IOS_5_0,
        OperatingSystemVersion.IOS_5_1,
        OperatingSystemVersion.IOS_6_0,
        OperatingSystemVersion.IOS_6_1,
        OperatingSystemVersion.IOS_7_0,
        OperatingSystemVersion.IOS_7_1,
        OperatingSystemVersion.IOS_8_0,
        OperatingSystemVersion.IOS_8_0,
        OperatingSystemVersion.IOS_8_1,
        OperatingSystemVersion.IOS_8_2,
        OperatingSystemVersion.IOS_8_3,
        OperatingSystemVersion.IOS_8_4,
        OperatingSystemVersion.IOS_9_0,
        OperatingSystemVersion.IOS_9_1,
        OperatingSystemVersion.IOS_9_2,
        OperatingSystemVersion.IOS_9_3,
        OperatingSystemVersion.IOS_10_0,
        OperatingSystemVersion.IOS_10_1,
        OperatingSystemVersion.IOS_10_2,
        OperatingSystemVersion.IOS_10_3,
        OperatingSystemVersion.IOS_11_0,
        OperatingSystemVersion.IOS_12_0,
        OperatingSystemVersion.IOS_12_1,
        OperatingSystemVersion.IOS_12_2,
        OperatingSystemVersion.IOS_12_3,
        OperatingSystemVersion.IOS_12_4,
        OperatingSystemVersion.IOS_13_0,
        OperatingSystemVersion.IOS_13_1,
        OperatingSystemVersion.IOS_13_2,
    ],
    OperatingSystem.WINPHONE: [
        OperatingSystemVersion.WINPHONE_7,
        OperatingSystemVersion.WINPHONE_8_0,
        OperatingSystemVersion.WINPHONE_8_1,
        OperatingSystemVersion.WINPHONE_10,
    ],
    OperatingSystem.WINDOWS: [
        OperatingSystemVersion.WINDOWS_98,
        OperatingSystemVersion.WINDOWS_2000,
        OperatingSystemVersion.WINDOWS_XP,
        OperatingSystemVersion.WINDOWS_VISTA,
        OperatingSystemVersion.WINDOWS_7,
        OperatingSystemVersion.WINDOWS_8,
        OperatingSystemVersion.WINDOWS_8_1,
        OperatingSystemVersion.WINDOWS_10,
    ],
    OperatingSystem.MACOSX: [
        OperatingSystemVersion.MACOSX_10_4,
        OperatingSystemVersion.MACOSX_10_5,
        OperatingSystemVersion.MACOSX_10_6,
        OperatingSystemVersion.MACOSX_10_7,
        OperatingSystemVersion.MACOSX_10_8,
        OperatingSystemVersion.MACOSX_10_9,
        OperatingSystemVersion.MACOSX_10_10,
        OperatingSystemVersion.MACOSX_10_11,
        OperatingSystemVersion.MACOSX_10_12,
        OperatingSystemVersion.MACOSX_10_13,
        OperatingSystemVersion.MACOSX_10_14,
        OperatingSystemVersion.MACOSX_10_15,
    ],
}


class BrowserFamily(ConstantBase):
    UNKNOWN = None
    OTHER = "OTHER"
    CHROME = "CHROME"
    FIREFOX = "FIREFOX"
    SAFARI = "SAFARI"
    IE = "IE"
    SAMSUNG = "SAMSUNG"
    OPERA = "OPERA"
    UC_BROWSER = "UC_BROWSER"
    IN_APP = "IN_APP"
    EDGE = "EDGE"

    _VALUES = {
        UNKNOWN: "Not reported",
        OTHER: "Other",
        CHROME: "Chrome",
        FIREFOX: "Firefox",
        SAFARI: "Safari",
        IE: "Internet Explorer",
        SAMSUNG: "Samsung",
        OPERA: "Opera",
        UC_BROWSER: "UC Browser",
        IN_APP: "In App",
        EDGE: "Edge",
    }


class Environment(ConstantBase):
    UNKNOWN = None
    APP = "app"
    SITE = "site"

    _VALUES = dict(AdTargetEnvironment._VALUES)
    _VALUES.update({UNKNOWN: "Unknown"})


class ConnectionType(ConstantBase):
    UNKNOWN = None
    WIFI = "wifi"
    CELLULAR = "cellular"

    _VALUES = {UNKNOWN: "Not reported", WIFI: "Wi-Fi", CELLULAR: "Cellular"}


class PlacementType(ConstantBase):
    UNDEFINED = None
    IN_FEED = 1
    IN_ARTICLE_PAGE = 2
    ADS_SECTION = 3
    RECOMMENDATION_WIDGET = 4

    _VALUES = {
        UNDEFINED: "Not reported",
        IN_FEED: "In feed",
        IN_ARTICLE_PAGE: "In article page",
        ADS_SECTION: "Ads section",
        RECOMMENDATION_WIDGET: "Recommendation widget",
    }

    @classmethod
    def human_readable(cls, placement_type):
        return cls.get_text(placement_type) or "Other"


class ZemPlacementType(ConstantBase):
    UNKNOWN = None
    IN_APP = 1
    IN_FEED_WITH_IMAGE = 2
    SINGLE_TEXT_ONLY_AD = 3
    RECOMMENDATION_WIDGET_WITH_IMAGE = 4
    RECOMMENDATION_WIDGET_TEXT_ONLY = 5
    AD_BLOCKER = 6
    NEWSLETTER = 7

    _VALUES = {
        UNKNOWN: "Unknown",
        IN_APP: "In-App",
        IN_FEED_WITH_IMAGE: "In-Feed With Image",
        SINGLE_TEXT_ONLY_AD: "Single Text-Only Ad",
        RECOMMENDATION_WIDGET_WITH_IMAGE: "Recommendation Widget With Image",
        RECOMMENDATION_WIDGET_TEXT_ONLY: "Recommendation Widget Text Only",
        AD_BLOCKER: "Ad Blocker",
        NEWSLETTER: "Newsletter",
    }


class VideoPlaybackMethod(ConstantBase):
    UNKNOWN = None
    PAGE_LOAD_SOUND_ON = 1
    PAGE_LOAD_SOUND_OFF = 2
    ON_CLICK_SOUND_ON = 3
    ON_MOUSE_OVER_SOUND_ON = 4
    ON_VIEWPORT_ENTER_SOUND_ON = 5
    ON_VIEWPORT_ENTER_SOUND_OFF = 6

    _VALUES = {
        UNKNOWN: "Unknown",
        PAGE_LOAD_SOUND_ON: "Page Load Sound On",
        PAGE_LOAD_SOUND_OFF: "Page Load Sound Off",
        ON_CLICK_SOUND_ON: "On Click Sound On",
        ON_MOUSE_OVER_SOUND_ON: "On Mouse Over Sound On",
        ON_VIEWPORT_ENTER_SOUND_ON: "On Viewport Enter Sound On",
        ON_VIEWPORT_ENTER_SOUND_OFF: "On Viewport Enter Sound Off",
    }


class AdGroupDeliveryType(ConstantBase):
    STANDARD = 1
    ACCELERATED = 2

    _VALUES = {STANDARD: "Standard", ACCELERATED: "Accelerated"}


class SourceSubmissionPolicy(ConstantBase):
    AUTOMATIC = 1
    AUTOMATIC_WITH_AMPLIFY_APPROVAL = 3  # force ordering
    MANUAL = 2

    _VALUES = {
        AUTOMATIC: "Automatic",
        MANUAL: "Manual",
        AUTOMATIC_WITH_AMPLIFY_APPROVAL: "Automatic with Amplify approval",
    }


class Customflags(ConstantBase):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOL = "boolean"

    _VALUES = {INT: "number", FLOAT: "decimal number", STRING: "text", BOOL: "boolean"}


class Business(ConstantBase):
    Z1 = "z1"
    OEN = "oen"
    ZMS = "zms"
    NAS = "nas"
    INTERNAL = "internal"

    _VALUES = {
        Z1: "Zemanta One",
        OEN: "Outbrain Extended Network",
        ZMS: "Zemanta Managed Service",
        NAS: "Native Ad Server",
        INTERNAL: "Internal businesses",
    }


class DayHour(ConstantBase):
    MONDAY_0 = "monday_0"
    MONDAY_1 = "monday_1"
    MONDAY_2 = "monday_2"
    MONDAY_3 = "monday_3"
    MONDAY_4 = "monday_4"
    MONDAY_5 = "monday_5"
    MONDAY_6 = "monday_6"
    MONDAY_7 = "monday_7"
    MONDAY_8 = "monday_8"
    MONDAY_9 = "monday_9"
    MONDAY_10 = "monday_10"
    MONDAY_11 = "monday_11"
    MONDAY_12 = "monday_12"
    MONDAY_13 = "monday_13"
    MONDAY_14 = "monday_14"
    MONDAY_15 = "monday_15"
    MONDAY_16 = "monday_16"
    MONDAY_17 = "monday_17"
    MONDAY_18 = "monday_18"
    MONDAY_19 = "monday_19"
    MONDAY_20 = "monday_20"
    MONDAY_21 = "monday_21"
    MONDAY_22 = "monday_22"
    MONDAY_23 = "monday_23"
    TUESDAY_0 = "tuesday_0"
    TUESDAY_1 = "tuesday_1"
    TUESDAY_2 = "tuesday_2"
    TUESDAY_3 = "tuesday_3"
    TUESDAY_4 = "tuesday_4"
    TUESDAY_5 = "tuesday_5"
    TUESDAY_6 = "tuesday_6"
    TUESDAY_7 = "tuesday_7"
    TUESDAY_8 = "tuesday_8"
    TUESDAY_9 = "tuesday_9"
    TUESDAY_10 = "tuesday_10"
    TUESDAY_11 = "tuesday_11"
    TUESDAY_12 = "tuesday_12"
    TUESDAY_13 = "tuesday_13"
    TUESDAY_14 = "tuesday_14"
    TUESDAY_15 = "tuesday_15"
    TUESDAY_16 = "tuesday_16"
    TUESDAY_17 = "tuesday_17"
    TUESDAY_18 = "tuesday_18"
    TUESDAY_19 = "tuesday_19"
    TUESDAY_20 = "tuesday_20"
    TUESDAY_21 = "tuesday_21"
    TUESDAY_22 = "tuesday_22"
    TUESDAY_23 = "tuesday_23"
    WEDNESDAY_0 = "wednesday_0"
    WEDNESDAY_1 = "wednesday_1"
    WEDNESDAY_2 = "wednesday_2"
    WEDNESDAY_3 = "wednesday_3"
    WEDNESDAY_4 = "wednesday_4"
    WEDNESDAY_5 = "wednesday_5"
    WEDNESDAY_6 = "wednesday_6"
    WEDNESDAY_7 = "wednesday_7"
    WEDNESDAY_8 = "wednesday_8"
    WEDNESDAY_9 = "wednesday_9"
    WEDNESDAY_10 = "wednesday_10"
    WEDNESDAY_11 = "wednesday_11"
    WEDNESDAY_12 = "wednesday_12"
    WEDNESDAY_13 = "wednesday_13"
    WEDNESDAY_14 = "wednesday_14"
    WEDNESDAY_15 = "wednesday_15"
    WEDNESDAY_16 = "wednesday_16"
    WEDNESDAY_17 = "wednesday_17"
    WEDNESDAY_18 = "wednesday_18"
    WEDNESDAY_19 = "wednesday_19"
    WEDNESDAY_20 = "wednesday_20"
    WEDNESDAY_21 = "wednesday_21"
    WEDNESDAY_22 = "wednesday_22"
    WEDNESDAY_23 = "wednesday_23"
    THURSDAY_0 = "thursday_0"
    THURSDAY_1 = "thursday_1"
    THURSDAY_2 = "thursday_2"
    THURSDAY_3 = "thursday_3"
    THURSDAY_4 = "thursday_4"
    THURSDAY_5 = "thursday_5"
    THURSDAY_6 = "thursday_6"
    THURSDAY_7 = "thursday_7"
    THURSDAY_8 = "thursday_8"
    THURSDAY_9 = "thursday_9"
    THURSDAY_10 = "thursday_10"
    THURSDAY_11 = "thursday_11"
    THURSDAY_12 = "thursday_12"
    THURSDAY_13 = "thursday_13"
    THURSDAY_14 = "thursday_14"
    THURSDAY_15 = "thursday_15"
    THURSDAY_16 = "thursday_16"
    THURSDAY_17 = "thursday_17"
    THURSDAY_18 = "thursday_18"
    THURSDAY_19 = "thursday_19"
    THURSDAY_20 = "thursday_20"
    THURSDAY_21 = "thursday_21"
    THURSDAY_22 = "thursday_22"
    THURSDAY_23 = "thursday_23"
    FRIDAY_0 = "friday_0"
    FRIDAY_1 = "friday_1"
    FRIDAY_2 = "friday_2"
    FRIDAY_3 = "friday_3"
    FRIDAY_4 = "friday_4"
    FRIDAY_5 = "friday_5"
    FRIDAY_6 = "friday_6"
    FRIDAY_7 = "friday_7"
    FRIDAY_8 = "friday_8"
    FRIDAY_9 = "friday_9"
    FRIDAY_10 = "friday_10"
    FRIDAY_11 = "friday_11"
    FRIDAY_12 = "friday_12"
    FRIDAY_13 = "friday_13"
    FRIDAY_14 = "friday_14"
    FRIDAY_15 = "friday_15"
    FRIDAY_16 = "friday_16"
    FRIDAY_17 = "friday_17"
    FRIDAY_18 = "friday_18"
    FRIDAY_19 = "friday_19"
    FRIDAY_20 = "friday_20"
    FRIDAY_21 = "friday_21"
    FRIDAY_22 = "friday_22"
    FRIDAY_23 = "friday_23"
    SATURDAY_0 = "saturday_0"
    SATURDAY_1 = "saturday_1"
    SATURDAY_2 = "saturday_2"
    SATURDAY_3 = "saturday_3"
    SATURDAY_4 = "saturday_4"
    SATURDAY_5 = "saturday_5"
    SATURDAY_6 = "saturday_6"
    SATURDAY_7 = "saturday_7"
    SATURDAY_8 = "saturday_8"
    SATURDAY_9 = "saturday_9"
    SATURDAY_10 = "saturday_10"
    SATURDAY_11 = "saturday_11"
    SATURDAY_12 = "saturday_12"
    SATURDAY_13 = "saturday_13"
    SATURDAY_14 = "saturday_14"
    SATURDAY_15 = "saturday_15"
    SATURDAY_16 = "saturday_16"
    SATURDAY_17 = "saturday_17"
    SATURDAY_18 = "saturday_18"
    SATURDAY_19 = "saturday_19"
    SATURDAY_20 = "saturday_20"
    SATURDAY_21 = "saturday_21"
    SATURDAY_22 = "saturday_22"
    SATURDAY_23 = "saturday_23"
    SUNDAY_0 = "sunday_0"
    SUNDAY_1 = "sunday_1"
    SUNDAY_2 = "sunday_2"
    SUNDAY_3 = "sunday_3"
    SUNDAY_4 = "sunday_4"
    SUNDAY_5 = "sunday_5"
    SUNDAY_6 = "sunday_6"
    SUNDAY_7 = "sunday_7"
    SUNDAY_8 = "sunday_8"
    SUNDAY_9 = "sunday_9"
    SUNDAY_10 = "sunday_10"
    SUNDAY_11 = "sunday_11"
    SUNDAY_12 = "sunday_12"
    SUNDAY_13 = "sunday_13"
    SUNDAY_14 = "sunday_14"
    SUNDAY_15 = "sunday_15"
    SUNDAY_16 = "sunday_16"
    SUNDAY_17 = "sunday_17"
    SUNDAY_18 = "sunday_18"
    SUNDAY_19 = "sunday_19"
    SUNDAY_20 = "sunday_20"
    SUNDAY_21 = "sunday_21"
    SUNDAY_22 = "sunday_22"
    SUNDAY_23 = "sunday_23"

    _VALUES = {
        MONDAY_0: "Monday 0:00 - 1:00",
        MONDAY_1: "Monday 1:00 - 2:00",
        MONDAY_2: "Monday 2:00 - 3:00",
        MONDAY_3: "Monday 3:00 - 4:00",
        MONDAY_4: "Monday 4:00 - 5:00",
        MONDAY_5: "Monday 5:00 - 6:00",
        MONDAY_6: "Monday 6:00 - 7:00",
        MONDAY_7: "Monday 7:00 - 8:00",
        MONDAY_8: "Monday 8:00 - 9:00",
        MONDAY_9: "Monday 9:00 - 10:00",
        MONDAY_10: "Monday 10:00 - 11:00",
        MONDAY_11: "Monday 11:00 - 12:00",
        MONDAY_12: "Monday 12:00 - 13:00",
        MONDAY_13: "Monday 13:00 - 14:00",
        MONDAY_14: "Monday 14:00 - 15:00",
        MONDAY_15: "Monday 15:00 - 16:00",
        MONDAY_16: "Monday 16:00 - 17:00",
        MONDAY_17: "Monday 17:00 - 18:00",
        MONDAY_18: "Monday 18:00 - 19:00",
        MONDAY_19: "Monday 19:00 - 20:00",
        MONDAY_20: "Monday 20:00 - 21:00",
        MONDAY_21: "Monday 21:00 - 22:00",
        MONDAY_22: "Monday 22:00 - 23:00",
        MONDAY_23: "Monday 23:00 - 24:00",
        TUESDAY_0: "Tuesday 0:00 - 1:00",
        TUESDAY_1: "Tuesday 1:00 - 2:00",
        TUESDAY_2: "Tuesday 2:00 - 3:00",
        TUESDAY_3: "Tuesday 3:00 - 4:00",
        TUESDAY_4: "Tuesday 4:00 - 5:00",
        TUESDAY_5: "Tuesday 5:00 - 6:00",
        TUESDAY_6: "Tuesday 6:00 - 7:00",
        TUESDAY_7: "Tuesday 7:00 - 8:00",
        TUESDAY_8: "Tuesday 8:00 - 9:00",
        TUESDAY_9: "Tuesday 9:00 - 10:00",
        TUESDAY_10: "Tuesday 10:00 - 11:00",
        TUESDAY_11: "Tuesday 11:00 - 12:00",
        TUESDAY_12: "Tuesday 12:00 - 13:00",
        TUESDAY_13: "Tuesday 13:00 - 14:00",
        TUESDAY_14: "Tuesday 14:00 - 15:00",
        TUESDAY_15: "Tuesday 15:00 - 16:00",
        TUESDAY_16: "Tuesday 16:00 - 17:00",
        TUESDAY_17: "Tuesday 17:00 - 18:00",
        TUESDAY_18: "Tuesday 18:00 - 19:00",
        TUESDAY_19: "Tuesday 19:00 - 20:00",
        TUESDAY_20: "Tuesday 20:00 - 21:00",
        TUESDAY_21: "Tuesday 21:00 - 22:00",
        TUESDAY_22: "Tuesday 22:00 - 23:00",
        TUESDAY_23: "Tuesday 23:00 - 24:00",
        WEDNESDAY_0: "Wednesday 0:00 - 1:00",
        WEDNESDAY_1: "Wednesday 1:00 - 2:00",
        WEDNESDAY_2: "Wednesday 2:00 - 3:00",
        WEDNESDAY_3: "Wednesday 3:00 - 4:00",
        WEDNESDAY_4: "Wednesday 4:00 - 5:00",
        WEDNESDAY_5: "Wednesday 5:00 - 6:00",
        WEDNESDAY_6: "Wednesday 6:00 - 7:00",
        WEDNESDAY_7: "Wednesday 7:00 - 8:00",
        WEDNESDAY_8: "Wednesday 8:00 - 9:00",
        WEDNESDAY_9: "Wednesday 9:00 - 10:00",
        WEDNESDAY_10: "Wednesday 10:00 - 11:00",
        WEDNESDAY_11: "Wednesday 11:00 - 12:00",
        WEDNESDAY_12: "Wednesday 12:00 - 13:00",
        WEDNESDAY_13: "Wednesday 13:00 - 14:00",
        WEDNESDAY_14: "Wednesday 14:00 - 15:00",
        WEDNESDAY_15: "Wednesday 15:00 - 16:00",
        WEDNESDAY_16: "Wednesday 16:00 - 17:00",
        WEDNESDAY_17: "Wednesday 17:00 - 18:00",
        WEDNESDAY_18: "Wednesday 18:00 - 19:00",
        WEDNESDAY_19: "Wednesday 19:00 - 20:00",
        WEDNESDAY_20: "Wednesday 20:00 - 21:00",
        WEDNESDAY_21: "Wednesday 21:00 - 22:00",
        WEDNESDAY_22: "Wednesday 22:00 - 23:00",
        WEDNESDAY_23: "Wednesday 23:00 - 24:00",
        THURSDAY_0: "Thursday 0:00 - 1:00",
        THURSDAY_1: "Thursday 1:00 - 2:00",
        THURSDAY_2: "Thursday 2:00 - 3:00",
        THURSDAY_3: "Thursday 3:00 - 4:00",
        THURSDAY_4: "Thursday 4:00 - 5:00",
        THURSDAY_5: "Thursday 5:00 - 6:00",
        THURSDAY_6: "Thursday 6:00 - 7:00",
        THURSDAY_7: "Thursday 7:00 - 8:00",
        THURSDAY_8: "Thursday 8:00 - 9:00",
        THURSDAY_9: "Thursday 9:00 - 10:00",
        THURSDAY_10: "Thursday 10:00 - 11:00",
        THURSDAY_11: "Thursday 11:00 - 12:00",
        THURSDAY_12: "Thursday 12:00 - 13:00",
        THURSDAY_13: "Thursday 13:00 - 14:00",
        THURSDAY_14: "Thursday 14:00 - 15:00",
        THURSDAY_15: "Thursday 15:00 - 16:00",
        THURSDAY_16: "Thursday 16:00 - 17:00",
        THURSDAY_17: "Thursday 17:00 - 18:00",
        THURSDAY_18: "Thursday 18:00 - 19:00",
        THURSDAY_19: "Thursday 19:00 - 20:00",
        THURSDAY_20: "Thursday 20:00 - 21:00",
        THURSDAY_21: "Thursday 21:00 - 22:00",
        THURSDAY_22: "Thursday 22:00 - 23:00",
        THURSDAY_23: "Thursday 23:00 - 24:00",
        FRIDAY_0: "Friday 0:00 - 1:00",
        FRIDAY_1: "Friday 1:00 - 2:00",
        FRIDAY_2: "Friday 2:00 - 3:00",
        FRIDAY_3: "Friday 3:00 - 4:00",
        FRIDAY_4: "Friday 4:00 - 5:00",
        FRIDAY_5: "Friday 5:00 - 6:00",
        FRIDAY_6: "Friday 6:00 - 7:00",
        FRIDAY_7: "Friday 7:00 - 8:00",
        FRIDAY_8: "Friday 8:00 - 9:00",
        FRIDAY_9: "Friday 9:00 - 10:00",
        FRIDAY_10: "Friday 10:00 - 11:00",
        FRIDAY_11: "Friday 11:00 - 12:00",
        FRIDAY_12: "Friday 12:00 - 13:00",
        FRIDAY_13: "Friday 13:00 - 14:00",
        FRIDAY_14: "Friday 14:00 - 15:00",
        FRIDAY_15: "Friday 15:00 - 16:00",
        FRIDAY_16: "Friday 16:00 - 17:00",
        FRIDAY_17: "Friday 17:00 - 18:00",
        FRIDAY_18: "Friday 18:00 - 19:00",
        FRIDAY_19: "Friday 19:00 - 20:00",
        FRIDAY_20: "Friday 20:00 - 21:00",
        FRIDAY_21: "Friday 21:00 - 22:00",
        FRIDAY_22: "Friday 22:00 - 23:00",
        FRIDAY_23: "Friday 23:00 - 24:00",
        SATURDAY_0: "Saturday 0:00 - 1:00",
        SATURDAY_1: "Saturday 1:00 - 2:00",
        SATURDAY_2: "Saturday 2:00 - 3:00",
        SATURDAY_3: "Saturday 3:00 - 4:00",
        SATURDAY_4: "Saturday 4:00 - 5:00",
        SATURDAY_5: "Saturday 5:00 - 6:00",
        SATURDAY_6: "Saturday 6:00 - 7:00",
        SATURDAY_7: "Saturday 7:00 - 8:00",
        SATURDAY_8: "Saturday 8:00 - 9:00",
        SATURDAY_9: "Saturday 9:00 - 10:00",
        SATURDAY_10: "Saturday 10:00 - 11:00",
        SATURDAY_11: "Saturday 11:00 - 12:00",
        SATURDAY_12: "Saturday 12:00 - 13:00",
        SATURDAY_13: "Saturday 13:00 - 14:00",
        SATURDAY_14: "Saturday 14:00 - 15:00",
        SATURDAY_15: "Saturday 15:00 - 16:00",
        SATURDAY_16: "Saturday 16:00 - 17:00",
        SATURDAY_17: "Saturday 17:00 - 18:00",
        SATURDAY_18: "Saturday 18:00 - 19:00",
        SATURDAY_19: "Saturday 19:00 - 20:00",
        SATURDAY_20: "Saturday 20:00 - 21:00",
        SATURDAY_21: "Saturday 21:00 - 22:00",
        SATURDAY_22: "Saturday 22:00 - 23:00",
        SATURDAY_23: "Saturday 23:00 - 24:00",
        SUNDAY_0: "Sunday 0:00 - 1:00",
        SUNDAY_1: "Sunday 1:00 - 2:00",
        SUNDAY_2: "Sunday 2:00 - 3:00",
        SUNDAY_3: "Sunday 3:00 - 4:00",
        SUNDAY_4: "Sunday 4:00 - 5:00",
        SUNDAY_5: "Sunday 5:00 - 6:00",
        SUNDAY_6: "Sunday 6:00 - 7:00",
        SUNDAY_7: "Sunday 7:00 - 8:00",
        SUNDAY_8: "Sunday 8:00 - 9:00",
        SUNDAY_9: "Sunday 9:00 - 10:00",
        SUNDAY_10: "Sunday 10:00 - 11:00",
        SUNDAY_11: "Sunday 11:00 - 12:00",
        SUNDAY_12: "Sunday 12:00 - 13:00",
        SUNDAY_13: "Sunday 13:00 - 14:00",
        SUNDAY_14: "Sunday 14:00 - 15:00",
        SUNDAY_15: "Sunday 15:00 - 16:00",
        SUNDAY_16: "Sunday 16:00 - 17:00",
        SUNDAY_17: "Sunday 17:00 - 18:00",
        SUNDAY_18: "Sunday 18:00 - 19:00",
        SUNDAY_19: "Sunday 19:00 - 20:00",
        SUNDAY_20: "Sunday 20:00 - 21:00",
        SUNDAY_21: "Sunday 21:00 - 22:00",
        SUNDAY_22: "Sunday 22:00 - 23:00",
        SUNDAY_23: "Sunday 23:00 - 24:00",
    }


class StatsDatabaseType(ConstantBase):
    POSTGRES = "POSTGRES"
    HOT_CLUSTER = "HOT_CLUSTER"
    COLD_CLUSTER = "COLD_CLUSTER"

    _VALUES = {POSTGRES: "POSTGRES", HOT_CLUSTER: "HOT_CLUSTER", COLD_CLUSTER: "COLD CLUSTER,"}
