import dash.regions
from utils import dates_helper
from utils.constant_base import ConstantBase

START_YEAR = 1991


class CompanyType(ConstantBase):
    AGENCY = 1
    AD_NETWORK = 2
    BRAND_DIRECT_ADVERTISER = 3
    AFFILIATE = 4
    PUBLISHER = 5
    OTHER = 6

    _VALUES = {
        AGENCY: "Agency",
        AD_NETWORK: "Ad Network",
        BRAND_DIRECT_ADVERTISER: "Brand/Direct Advertiser",
        AFFILIATE: "Affiliate",
        PUBLISHER: "Publisher",
        OTHER: "Other",
    }


class Country(ConstantBase):
    _VALUES = dict(list(dash.regions.COUNTRY_BY_CODE.items()))

    @classmethod
    def _get_all_kv_pairs(cls):
        return [(key, key) for key, value in cls._VALUES.items()]


class Year(ConstantBase):
    _VALUES = dict(((year, year) for year in list(reversed(range(START_YEAR, dates_helper.local_today().year + 1)))))

    @classmethod
    def _get_all_kv_pairs(cls):
        return [(key, key) for key, value in cls._VALUES.items()]


class ProgrammaticPlatform(ConstantBase):
    ADOBE = 1
    AMAZON = 2
    APPNEXUS = 3
    THETRADEDESK = 4
    GOOGLE = 5
    MEDIAMATH = 6
    OTHER = 7
    NA = 8

    _VALUES = {
        ADOBE: "Adobe",
        AMAZON: "Amazon",
        APPNEXUS: "Xandr (Appnexus)",
        THETRADEDESK: "TheTradeDesk",
        GOOGLE: "DV360 (Google)",
        MEDIAMATH: "Mediamath",
        OTHER: "Other",
        NA: "N/A",
    }


class Status(ConstantBase):
    INVITATION_PENDING = 1
    ACTIVE = 2

    _VALUES = {INVITATION_PENDING: "Invitation Pending", ACTIVE: "Active"}
