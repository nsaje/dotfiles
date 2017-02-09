# -*- coding: utf-8 -*-
from utils.constant_base import ConstantBase
from dash import regions
from decimal import Decimal


# Outbrain supports only 10 blocked publisher per marketer id
# which corresponds to 10 blacklisted publishers per Z1 account
# Experiment 6/13/2016: we can blacklist 30 publishers on OB dashboard, it's not documented
#                       but we can try to enable 30 via API
MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD = 30

MAX_CONVERSION_GOALS_PER_CAMPAIGN = 15

GA_PROPERTY_ID_REGEX = r'UA-([0-9]+)-([0-9]+)'
DEFAULT_CALL_TO_ACTION = 'Read more'


class AdGroupSettingsState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class AdGroupRunningStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Active',
        INACTIVE: 'Paused'
    }


class AdGroupSettingsAutopilotState(ConstantBase):
    ACTIVE_CPC_BUDGET = 1
    INACTIVE = 2
    ACTIVE_CPC = 3

    _VALUES = {
        ACTIVE_CPC: 'Optimize Bids',
        ACTIVE_CPC_BUDGET: 'Optimize Bids and Daily Spend Caps',
        INACTIVE: 'Disabled'
    }


class AdGroupSourceSettingsState(ConstantBase):
    # keep in sync with zwei
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class ExportStatus(ConstantBase):
    # Generalized constant used for export output formatting. It handles conversion to text for various state classes.
    ACTIVE = 1
    INACTIVE = 2
    ARCHIVED = 3

    _VALUES = {
        ACTIVE: 'Active',
        INACTIVE: 'Inactive',
        ARCHIVED: 'Archived'
    }


class AdTargetDevice(ConstantBase):
    DESKTOP = 'desktop'
    TABLET = 'tablet'
    MOBILE = 'mobile'

    _VALUES = {
        DESKTOP: 'Desktop',
        TABLET: 'Tablet',
        MOBILE: 'Mobile'
    }


class AdTargetLocation(ConstantBase):
    _VALUES = dict(regions.COUNTRY_BY_CODE.items() + regions.DMA_BY_CODE.items() + regions.SUBDIVISION_BY_CODE.items())

    @classmethod
    def get_choices(cls):
        return cls._VALUES.items()


class ContentAdSubmissionStatus(ConstantBase):
    NOT_SUBMITTED = -1
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    LIMIT_REACHED = 4

    _VALUES = {
        NOT_SUBMITTED: 'Not submitted',
        PENDING: 'Pending',
        APPROVED: 'Approved',
        REJECTED: 'Rejected',
        LIMIT_REACHED: 'Limit reached',
    }


class ContentAdSourceState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused'
    }


class PublisherStatus(ConstantBase):
    ENABLED = 1
    BLACKLISTED = 2
    PENDING = 3

    _VALUES = {
        ENABLED: 'Active',
        BLACKLISTED: 'Blacklisted',
        PENDING: 'Pending'
    }


class AccountType(ConstantBase):
    UNKNOWN = 1
    TEST = 2
    SANDBOX = 3
    PILOT = 4
    ACTIVATED = 5
    MANAGED = 6

    _VALUES = {
        UNKNOWN: 'Unknown',
        TEST: 'Test',
        SANDBOX: 'Sandbox',
        PILOT: 'Pilot',
        ACTIVATED: 'Activated',
        MANAGED: 'Managed',
    }


class InfoboxLevel(ConstantBase):
    ADGROUP = 'adgroup'
    CAMPAIGN = 'campaign'
    ACCOUNT = 'account'
    ALL_ACCOUNTS = 'all-accounts'

    _VALUES = {
        ADGROUP: 'Ad Group',
        CAMPAIGN: 'Campaign',
        ACCOUNT: 'Account',
        ALL_ACCOUNTS: 'All Accounts'
    }


class InfoboxStatus(ConstantBase):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    STOPPED = 'stopped'
    LANDING_MODE = 'landing-mode'
    AUTOPILOT = 'autopilot'

    _VALUES = {
        ACTIVE: 'Active',
        INACTIVE: 'Inactive',
        STOPPED: 'Stopped',
        LANDING_MODE: 'Landing Mode',
        AUTOPILOT: 'Autopilot'
    }


class PublisherBlacklistLevel(ConstantBase):

    ADGROUP = 'adgroup'
    CAMPAIGN = 'campaign'
    ACCOUNT = 'account'
    GLOBAL = 'global'

    _INT_MAP = {
        ADGROUP: 1,
        CAMPAIGN: 2,
        ACCOUNT: 3,
        GLOBAL: 4
    }

    _VALUES = {
        ADGROUP: 'Adgroup',
        CAMPAIGN: 'Campaign',
        ACCOUNT: 'Account',
        GLOBAL: 'Global'
    }

    @classmethod
    def verbose(cls, level):
        level_verbose = "Blacklisted in this ad group"
        if level == PublisherBlacklistLevel.CAMPAIGN:
            level_verbose = "Blacklisted in this campaign"
        elif level == PublisherBlacklistLevel.ACCOUNT:
            level_verbose = "Blacklisted in this account"
        elif level == PublisherBlacklistLevel.GLOBAL:
            level_verbose = "Blacklisted globally"
        return level_verbose

    @classmethod
    def compare(cls, level, other):
        mapping = cls._INT_MAP
        return mapping[level].__cmp__(mapping[other])


class PublisherBlacklistFilter(ConstantBase):
    SHOW_ALL = 'all'
    SHOW_ACTIVE = 'active'
    SHOW_BLACKLISTED = 'blacklisted'

    _VALUES = {
        SHOW_ALL: 'All',
        SHOW_ACTIVE: 'Active',
        SHOW_BLACKLISTED: 'Blacklisted'
    }


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
        IAB5_4: "Colledge Administration",
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
        IAB26_4: "CopyrightInfringement",
    }


class InterestCategory(ConstantBase):
    ENTERTAINMENT = 'entertainment'
    FUN_QUIZZES = 'fun_quizzes'
    MUSIC = 'music'
    CARS = 'cars'
    FINANCE = 'finance'
    EDUCATION = 'education'
    FAMILY = 'family'
    HEALTH = 'health'
    FOOD = 'food'
    HOBBIES = 'hobbies'
    GAMES = 'games'
    HOME = 'home'
    POLITICS_LAW = 'politics_law'
    MEDIA = 'media'
    DATING = 'dating'
    SCIENCE = 'science'
    WEATHER = 'weather'
    PETS = 'pets'
    SPORTS = 'sports'
    FASHION = 'fashion'
    TECHNOLOGY = 'technology'
    UTILITY = 'utility'
    TRAVEL = 'travel'
    SHOPPING_COUPONS = 'shopping_coupons'
    RELIGION = 'religion'
    COMMUNICATION = 'communication'
    CAREER = 'career'
    PREMIUM = 'premium'
    WOMEN = 'women'
    MEN = 'men'

    # internal from here on
    FOREIGN = 'foreign'
    FRENCH = 'french'
    SPANISH = 'spanish'
    OTHER = 'other'
    UNKNOWN = '?'
    OUTBRAIN = 'outbrain'
    # this is a cisco specific thing and is set on the bidder based on page url keywords
    TECHNOLOGY_CONTEXTUAL = 'technology-contextual'
    FUN = 'fun'
    QUIZZES = 'quizzes'
    POLITICS = 'politics'
    LAW = 'law'
    COUPONS = 'coupons'
    SHOPPING = 'shopping'

    _VALUES = {
        ENTERTAINMENT: 'Arts & Entertainment',
        FUN_QUIZZES: 'Viral, lists & Quizzes',
        MUSIC: 'Music',
        CARS: 'Automotive',
        FINANCE: 'Business & Finance',
        EDUCATION: 'Education',
        FAMILY: 'Family & Parenting',
        HEALTH: 'Health & Fitness',
        FOOD: 'Food & Drink',
        HOBBIES: 'Hobbies & Interests',
        GAMES: 'Games & Gaming',
        HOME: 'Home & Garden',
        POLITICS_LAW: 'Law, Gov’t & Politics',
        MEDIA: 'News',
        DATING: 'Dating & Relationships',
        SCIENCE: 'Science',
        WEATHER: 'Weather & Environment',
        PETS: 'Pets',
        SPORTS: 'Sports',
        FASHION: 'Beauty & Fashion',
        TECHNOLOGY: 'Technology',
        UTILITY: 'Apps & Online services',
        TRAVEL: 'Travel',
        SHOPPING_COUPONS: 'Shopping',
        RELIGION: 'Religion & Spirituality',
        COMMUNICATION: 'Communication Tools',
        CAREER: 'Careers',
        PREMIUM: 'Premium',
        WOMEN: 'Women’s Lifestyle',
        MEN: 'Men’s Lifestyle',
        FOREIGN: 'Foreign',
        FRENCH: 'French',
        SPANISH: 'Spanish',
        OTHER: 'Other',
        UNKNOWN: 'Unknown',
        OUTBRAIN: 'Outbrain',
        TECHNOLOGY_CONTEXTUAL: 'Technology - Contextual',
        FUN: 'Fun & Entertaining Sites',
        QUIZZES: 'Quizzes',
        POLITICS: 'Gov’t & Politics',
        LAW: 'Law',
        COUPONS: 'Couponing',
        SHOPPING: 'Shopping',
    }


class PromotionGoal(ConstantBase):
    BRAND_BUILDING = 1
    TRAFFIC_ACQUISITION = 2
    CONVERSIONS = 3

    _VALUES = {
        BRAND_BUILDING: 'Brand Building',
        TRAFFIC_ACQUISITION: 'Traffic Acquisition',
        CONVERSIONS: 'Conversions'
    }


class CampaignGoal(ConstantBase):
    CPA = 1
    PERCENT_BOUNCE_RATE = 2
    NEW_UNIQUE_VISITORS = 3
    SECONDS_TIME_ON_SITE = 4
    PAGES_PER_SESSION = 5

    _VALUES = {
        CPA: 'CPA',
        PERCENT_BOUNCE_RATE: '% bounce rate',
        NEW_UNIQUE_VISITORS: 'new unique visitors',
        SECONDS_TIME_ON_SITE: 'seconds time on site',
        PAGES_PER_SESSION: 'pages per session'
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

    _VALUES = {
        TIME_ON_SITE: 'Time on Site - Seconds',
        MAX_BOUNCE_RATE: 'Max Bounce Rate',
        PAGES_PER_SESSION: 'Pageviews per Visit',
        CPA: '$CPA',
        CPC: 'CPC',
        #        CPM: '$CPM',
        NEW_UNIQUE_VISITORS: 'New Unique Visitors',
        CPV: 'Cost per Visit',
        CP_NON_BOUNCED_VISIT: 'Cost per Non-Bounced Visit',
    }


class CampaignGoalPerformance(ConstantBase):
    UNDERPERFORMING = 1
    AVERAGE = 2
    SUPERPERFORMING = 3

    _VALUES = {
        UNDERPERFORMING: 'Underperforming',
        AVERAGE: 'Average performance',
        SUPERPERFORMING: 'Superperforming',
    }


class Emoticon(ConstantBase):
    HAPPY = 1
    NEUTRAL = 2
    SAD = 3

    _VALUES = {
        HAPPY: 'Happy',
        SAD: 'Sad',
        NEUTRAL: 'Neutral',
    }


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
    CAN_SET_MAX_CPM = 20

    _VALUES = {
        CAN_UPDATE_STATE: 'Can update state',
        CAN_UPDATE_CPC: 'Can update CPC',
        CAN_UPDATE_DAILY_BUDGET_AUTOMATIC: 'Can update daily budget automatically',
        CAN_MANAGE_CONTENT_ADS: 'Can manage content ads',
        HAS_3RD_PARTY_DASHBOARD: 'Has 3rd party dashboard',
        CAN_MODIFY_START_DATE: 'Can modify start date',
        CAN_MODIFY_END_DATE: 'Can modify end date',
        CAN_MODIFY_DEVICE_TARGETING: 'Can modify device targeting',
        CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC: 'Can modify DMA and subdivision targeting automatically',
        CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL: 'Can modify DMA and subdivision targeting manually',
        CAN_MODIFY_COUNTRY_TARGETING: 'Can modify targeting by country',
        # CAN_MODIFY_TRACKING_CODES: 'Can modify tracking codes',
        CAN_MODIFY_AD_GROUP_NAME: 'Can modify adgroup name',
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_AUTOMATIC: 'Can modify ad group IAB category automatically',
        UPDATE_TRACKING_CODES_ON_CONTENT_ADS: 'Update tracking codes on content ads',
        CAN_UPDATE_DAILY_BUDGET_MANUAL: 'Can update daily budget manually',
        CAN_MODIFY_AD_GROUP_IAB_CATEGORY_MANUAL: 'Can modify ad group IAB category manually',
        CAN_FETCH_REPORT_BY_PUBLISHER: 'Can fetch report by publishers',
        CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC: 'Can modify publisher blacklist',
        CAN_SET_MAX_CPM: 'Can set max CPM',
    }


class SourceSubmissionType(ConstantBase):
    DEFAULT = 1
    AD_GROUP = 2
    BATCH = 3

    _VALUES = {
        DEFAULT: 'Default',
        AD_GROUP: 'One submission per ad group',
        BATCH: 'Submit whole batch at once'
    }


class SourceType(ConstantBase):
    ADBLADE = 'adblade'
    GRAVITY = 'gravity'
    NRELATE = 'nrelate'
    OUTBRAIN = 'outbrain'
    YAHOO = 'yahoo'
    ZEMANTA = 'zemanta'
    DISQUS = 'disqus'
    B1 = 'b1'
    FACEBOOK = 'facebook'

    _VALUES = {
        ADBLADE: 'AdBlade',
        GRAVITY: 'Gravity',
        NRELATE: 'nRelate',
        OUTBRAIN: 'Outbrain',
        YAHOO: 'Yahoo',
        ZEMANTA: 'Zemanta',
        B1: 'B1',
        FACEBOOK: 'Facebook',
    }


class ConversionGoalType(ConstantBase):
    PIXEL = 1
    GA = 2
    OMNITURE = 3

    _VALUES = {
        PIXEL: 'Conversion Pixel',
        GA: 'Google Analytics',
        OMNITURE: 'Adobe Analytics',
    }


class UploadBatchStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3
    CANCELLED = 4

    _VALUES = {
        DONE: 'Done',
        FAILED: 'Failed',
        IN_PROGRESS: 'In progress',
        CANCELLED: 'Cancelled',
    }


class UploadBatchType(ConstantBase):
    INSERT = 1
    EDIT = 2

    _VALUES = {
        INSERT: 'Insert',
        EDIT: 'Edit',
    }


class RegionType(ConstantBase):
    COUNTRY = 1
    SUBDIVISION = 2
    DMA = 3

    _VALUES = {
        COUNTRY: 'Country',
        SUBDIVISION: 'U.S. state',  # NOTE update when subdivisions other than U.S. states are added
        DMA: 'DMA',
    }


class CreditLineItemStatus(ConstantBase):
    SIGNED = 1  # Only adding BudgetLineItems is permitted
    PENDING = 2  # Internal "waiting" status, fields are editable
    CANCELED = 3  # Adding BudgetLineItems is not permitted

    _VALUES = {
        SIGNED: 'Signed',
        PENDING: 'Pending',
        CANCELED: 'Canceled',
    }


class BudgetLineItemState(ConstantBase):
    ACTIVE = 1
    PENDING = 2
    INACTIVE = 3
    DEPLETED = 4

    _VALUES = {
        ACTIVE: 'Active',
        PENDING: 'Pending',
        INACTIVE: 'Inactive',
        DEPLETED: 'Depleted',
    }


class ScheduledReportSendingFrequency(ConstantBase):
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3

    _VALUES = {
        DAILY: 'Daily',
        WEEKLY: 'Weekly',
        MONTHLY: 'Monthly'
    }


class ScheduledReportDayOfWeek(ConstantBase):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

    _VALUES = {
        MONDAY: 'Monday',
        TUESDAY: 'Tuesday',
        WEDNESDAY: 'Wednesday',
        THURSDAY: 'Thursday',
        FRIDAY: 'Friday',
        SATURDAY: 'Saturday',
        SUNDAY: 'Sunday',
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
        YESTERDAY: 'Yesterday',
        LAST_7_DAYS: 'Last 7 Days',
        LAST_30_DAYS: 'Last 30 Days',
        THIS_WEEK: 'This Week',
        LAST_WEEK: 'Last Week',
        THIS_MONTH: 'This Month',
        LAST_MONTH: 'Last Month',
    }


class ScheduledReportState(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2
    REMOVED = 3

    _VALUES = {
        ACTIVE: 'Enabled',
        INACTIVE: 'Paused',
        REMOVED: 'Removed'
    }


class ScheduledReportGranularity(ConstantBase):
    ALL_ACCOUNTS = 1
    ACCOUNT = 2
    CAMPAIGN = 3
    AD_GROUP = 4
    CONTENT_AD = 5

    _VALUES = {
        ALL_ACCOUNTS: 'All Accounts',
        ACCOUNT: 'Account',
        CAMPAIGN: 'Campaign',
        AD_GROUP: 'Ad Group',
        CONTENT_AD: 'Content Ad',
    }


class ScheduledReportLevel(ConstantBase):
    ALL_ACCOUNTS = 1
    ACCOUNT = 2
    CAMPAIGN = 3
    AD_GROUP = 4

    _VALUES = {
        ALL_ACCOUNTS: 'All Accounts',
        ACCOUNT: 'Account',
        CAMPAIGN: 'Campaign',
        AD_GROUP: 'Ad Group'
    }


class ScheduledReportSent(ConstantBase):
    SUCCESS = 1
    FAILED = 2

    _VALUES = {
        SUCCESS: 'Success',
        FAILED: 'Failed'
    }


class GATrackingType(ConstantBase):
    EMAIL = 1
    API = 2

    _VALUES = {
        EMAIL: 'Email',
        API: 'API'
    }


class SystemUserType(ConstantBase):
    CAMPAIGN_STOP = 1
    AUTOPILOT = 2
    K1_USER = 3

    _VALUES = {
        CAMPAIGN_STOP: 'Campaign Stop',
        AUTOPILOT: 'Zemanta Autopilot',
        K1_USER: 'System User '
    }


class FacebookPageRequestType(ConstantBase):
    EMPTY = 1
    CONNECTED = 2
    PENDING = 3
    INVALID = 4
    ERROR = 5

    _VALUES = {
        EMPTY: 'Empty',
        CONNECTED: 'Connected',
        PENDING: 'Pending',
        INVALID: 'Invalid',
        ERROR: 'Error'
    }


class AsyncUploadJobStatus(ConstantBase):
    PENDING_START = 1
    WAITING_RESPONSE = 2
    OK = 3
    FAILED = 4

    _VALUES = {
        PENDING_START: 'Pending',
        WAITING_RESPONSE: 'Waiting for response',
        OK: 'OK',
        FAILED: 'Failed',
    }


class DeviceType(ConstantBase):
    UNDEFINED = 0
    DESKTOP = 1
    TABLET = 2
    MOBILE = 3

    _VALUES = {
        UNDEFINED: 'Undefined',
        DESKTOP: 'Desktop',
        TABLET: 'Tablet',
        MOBILE: 'Mobile',
    }


class AgeGroup(ConstantBase):
    UNDEFINED = 0
    AGE_18_20 = 1
    AGE_21_29 = 2
    AGE_30_39 = 3
    AGE_40_49 = 4
    AGE_50_64 = 5
    AGE_65_MORE = 6

    _VALUES = {
        UNDEFINED: 'Undefined',
        AGE_18_20: '18-20',
        AGE_21_29: '21-29',
        AGE_30_39: '30-39',
        AGE_40_49: '40-49',
        AGE_50_64: '50-64',
        AGE_65_MORE: '65 and older',
    }


class Gender(ConstantBase):
    UNDEFINED = 0
    MEN = 1
    WOMEN = 2

    _VALUES = {
        UNDEFINED: 'Undefined',
        MEN: 'Men',
        WOMEN: 'Women',
    }


class AgeGenderGroup(ConstantBase):
    UNDEFINED = 0
    AGE_18_20_MEN = 1
    AGE_18_20_WOMEN = 2
    AGE_18_20_UNDEFINED = 3
    AGE_21_29_MEN = 4
    AGE_21_29_WOMEN = 5
    AGE_21_29_UNDEFINED = 6
    AGE_30_39_MEN = 7
    AGE_30_39_WOMEN = 8
    AGE_30_39_UNDEFINED = 9
    AGE_40_49_MEN = 10
    AGE_40_49_WOMEN = 11
    AGE_40_49_UNDEFINED = 12
    AGE_50_64_MEN = 13
    AGE_50_64_WOMEN = 14
    AGE_50_64_UNDEFINED = 15
    AGE_65_MORE_MEN = 16
    AGE_65_MORE_WOMEN = 17
    AGE_65_MORE_UNDEFINED = 18

    _VALUES = {
        UNDEFINED: 'Undefined',
        AGE_18_20_MEN: '18-20 Men',
        AGE_18_20_WOMEN: '18-20 Women',
        AGE_18_20_UNDEFINED: '18-20 Undefined',
        AGE_21_29_MEN: '21-29 Men',
        AGE_21_29_WOMEN: '21-29 Women',
        AGE_21_29_UNDEFINED: '21-29 Undefined',
        AGE_30_39_MEN: '30-39 Men',
        AGE_30_39_WOMEN: '30-39 Women',
        AGE_30_39_UNDEFINED: '30-39 Undefined',
        AGE_40_49_MEN: '40-49 Men',
        AGE_40_49_WOMEN: '40-49 Women',
        AGE_40_49_UNDEFINED: '40-49 Undefined',
        AGE_50_64_MEN: '50-64 Men',
        AGE_50_64_WOMEN: '50-64 Women',
        AGE_50_64_UNDEFINED: '50-64 Undefined',
        AGE_65_MORE_MEN: '65+ Men',
        AGE_65_MORE_WOMEN: '65+ Women',
        AGE_65_MORE_UNDEFINED: '65+ Undefined',
    }


class DMA(ConstantBase):
    _VALUES = {int(k): v for k, v in regions.DMA_BY_CODE.iteritems()}


class ConversionWindows(ConstantBase):
    LEQ_1_DAY = 24
    LEQ_7_DAYS = 168
    LEQ_30_DAYS = 720
    LEQ_90_DAYS = 2160

    _VALUES = {
        LEQ_1_DAY: '1 day',
        LEQ_7_DAYS: '7 days',
        LEQ_30_DAYS: '30 days',
        LEQ_90_DAYS: '90 days',
    }


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
    CAMPAIGN_LANDING_MODE_SWITCH = 13
    CAMPAIGN_BUDGET_LOW = 14
    DEMO_RUNNING = 15
    LIVESTREAM_SESSION = 16
    DAILY_MANAGEMENT_REPORT = 17
    OUTBRAIN_ACCOUNTS_RUNNING_OUT = 18
    GA_SETUP_INSTRUCTIONS = 19
    ASYNC_REPORT_RESULTS = 20

    _VALUES = {
        ADGROUP_CHANGE: 'Ad group settings change',
        CAMPAIGN_CHANGE: 'Campaign settings change',
        BUDGET_CHANGE: 'Budget change',
        PIXEL_ADD: 'New conversion pixel',
        PASSWORD_RESET: 'User password reset',
        USER_NEW: 'New user introduction email',
        SUPPLY_REPORT: 'Supply report',
        SCHEDULED_EXPORT_REPORT: 'Scheduled report',
        BUDGET_DEPLETING: 'Depleting budget notification',
        CAMPAIGN_STOPPED: 'Campaign stopped notification',
        AUTOPILOT_AD_GROUP_CHANGE: 'Autopilot changes notification',
        AUTOPILOT_AD_GROUP_BUDGET_INIT: 'Autopilot initialisation notification',
        CAMPAIGN_LANDING_MODE_SWITCH: 'Campaign switched to landing mode notification',
        CAMPAIGN_BUDGET_LOW: 'Campaign is running out of budget notification',
        DEMO_RUNNING: 'Demo is running',
        LIVESTREAM_SESSION: 'Livestream sesion id',
        DAILY_MANAGEMENT_REPORT: 'Daily management report',
        OUTBRAIN_ACCOUNTS_RUNNING_OUT: 'Unused Outbrain accounts running out',
        GA_SETUP_INSTRUCTIONS: 'Google Analytics Setup Instructions',
        ASYNC_REPORT_RESULTS: 'Report results',
    }


class ImageCrop(ConstantBase):
    CENTER = 'center'
    FACES = 'faces'
    ENTROPY = 'entropy'
    LEFT = 'left'
    RIGHT = 'right'
    TOP = 'top'
    BOTTOM = 'bottom'

    _VALUES = {
        CENTER: 'Center',
        FACES: 'Faces',
        ENTROPY: 'Entropy',
        LEFT: 'Left',
        RIGHT: 'Right',
        TOP: 'Top',
        BOTTOM: 'Bottom',
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
        AD_GROUP: 'Ad Group Level',
        CAMPAIGN: 'Campaign Level',
        ACCOUNT: 'Account Level',
        AGENCY: 'Agency Level',
        GLOBAL: 'All Accounts',
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
    CONVERSION_PIXEL_AUDIENCE_ENABLED = 21
    CONVERSION_PIXEL_SET_REDIRECT_URL = 23
    CONVERSION_PIXEL_REMOVE_REDIRECT_URL = 24

    _VALUES = {
        GOAL_CHANGE: 'Change Campaign Goal',
        BUDGET_CHANGE: 'Change Budget',
        CREDIT_CHANGE: 'Change Credit',
        PUBLISHER_BLACKLIST_CHANGE: 'Set Publisher Blacklist',
        GLOBAL_PUBLISHER_BLACKLIST_CHANGE: 'Set Global Publisher Blacklist',
        REPORTING_MANAGE: 'Manage Reporting',
        CONTENT_AD_STATE_CHANGE: 'Set Content Ad(s) State',
        SETTINGS_CHANGE: 'Change Settings',
        CREATE: 'Create',
        CONTENT_AD_CREATE: 'Create Content Ad',
        CONVERSION_PIXEL_CREATE: 'Create Conversion Pixel',
        CONVERSION_PIXEL_ARCHIVE_RESTORE: 'Archive/Restore Conversion Pixel',
        ARCHIVE_RESTORE: 'Archive/Restore',
        CONTENT_AD_ARCHIVE_RESTORE: 'Archive/Restore Content Ad(s)',
        MEDIA_SOURCE_SETTINGS_CHANGE: 'Set Media Source Settings',
        MEDIA_SOURCE_ADD: 'Add Media Source',
        CONVERSION_PIXEL_RENAME: 'Rename conversion pixel',
        AUDIENCE_CREATE: 'Create custom audience',
        AUDIENCE_ARCHIVE: 'Archive custom audience',
        AUDIENCE_RESTORE: 'Restore custom audience',
        AUDIENCE_UPDATE: 'Update custom audience',
        CONVERSION_PIXEL_AUDIENCE_ENABLED: 'Enable pixel for building audiences',
        CONVERSION_PIXEL_SET_REDIRECT_URL: 'Set redirect url for pixel',
        CONVERSION_PIXEL_REMOVE_REDIRECT_URL: 'Remove redirect url for pixel',
    }


class SlugType(ConstantBase):
    FACEBOOK = 'facebook'

    _VALUES = {
        FACEBOOK: 'Facebook'
    }


class FacebookAccountStatus(ConstantBase):
    # for the list of Facebook account status codes, check the page below:
    # https://developers.facebook.com/docs/marketing-api/reference/ad-account
    ACTIVE = 1
    DISABLED = 2
    UNSETTLED = 3
    PENDING_RISK_REVIEW = 7
    IN_GRACE_PERIOD = 9
    PENDING_CLOSURE = 100
    CLOSED = 101
    PENDING_SETTLEMENT = 102
    ANY_ACTIVE = 201
    ANY_CLOSED = 202

    _VALUES = {
        ACTIVE: 'active',
        DISABLED: 'disabled',
        UNSETTLED: 'unsettled',
        PENDING_RISK_REVIEW: 'pending risk review',
        IN_GRACE_PERIOD: 'in grace period',
        PENDING_CLOSURE: 'pending closure',
        CLOSED: 'closed',
        PENDING_SETTLEMENT: 'pending settlement',
        ANY_ACTIVE: 'any active',
        ANY_CLOSED: 'any closed'
    }


class AudienceRuleType(ConstantBase):
    STARTS_WITH = 1
    CONTAINS = 2
    NOT_STARTS_WITH = 3
    NOT_CONTAINS = 4
    VISIT = 5

    _VALUES = {
        STARTS_WITH: 'Starts with',
        CONTAINS: 'Contains',
        NOT_STARTS_WITH: 'Not starts with',
        NOT_CONTAINS: 'Not contains',
        VISIT: 'Visit',
    }


class Level(object):
    ALL_ACCOUNTS = 'all_accounts'
    ACCOUNTS = 'accounts'
    CAMPAIGNS = 'campaigns'
    AD_GROUPS = 'ad_groups'
    CONTENT_ADS = 'content_ads'


class AlertType(object):
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    DANGER = 'danger'


class ReportJobStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3
    CANCELLED = 4

    _VALUES = {
        DONE: 'Done',
        FAILED: 'Failed',
        IN_PROGRESS: 'In progress',
        CANCELLED: 'Cancelled',
    }


# MVP for all-RTB-sources-as-one
class SourceAllRTB(object):
    ID = '0123456789'
    NAME = 'RTB Sources'
    MAX_CPC = Decimal('7.0')
    MIN_CPC = Decimal('0.01')
    DECIMAL_PLACES = 4
    DEFAULT_DAILY_BUDGET = Decimal('50.00')
    DEFAULT_CPC_CC = Decimal('0.4500')
    MIN_DAILY_BUDGET = Decimal('1.00')
    MAX_DAILY_BUDGET = Decimal('10000.00')


class CpcConstraintType(ConstantBase):
    MANUAL = 1
    OUTBRAIN_BLACKLIST = 2

    _VALUES = {
        MANUAL: 'Manual',
        OUTBRAIN_BLACKLIST: 'Outbrain blacklist',
    }


class PublisherTargetingStatus(ConstantBase):
    WHITELISTED = 1
    BLACKLISTED = 2
    UNLISTED = 3

    _VALUES = {
        WHITELISTED: 'Whitelisted',
        BLACKLISTED: 'Blacklisted',
        UNLISTED: 'Active',
    }


class Service(ConstantBase):
    Z1 = 'z1'
    K1 = 'k1'
    R1 = 'r1'
    B1 = 'b1'

    _VALUES = {
        Z1: 'Zemanta One',
        K1: 'Konsistency One',
        R1: 'Redirector',
        B1: 'Bidder',
    }
