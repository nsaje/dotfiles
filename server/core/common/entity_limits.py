from collections import defaultdict

from django.conf import settings
from django.core.exceptions import PermissionDenied

DEFAULT_LIMITS = {
    "Account": 500,
    "Campaign": 500,
    "AdGroup": 500,
    "ContentAd": 500,
    "CampaignGoal": 50,
    "BudgetLineItem": 100,
    "PublisherGroup": 500,
    "PublisherGroupEntry": 100000,
    "ConversionPixel": 20,
    "DirectDeal": 100000,
    "Rule": 500,
}

ACCOUNT_EXCEPTIONS = defaultdict(
    dict,
    {
        "Campaign": {settings.HARDCODED_ACCOUNT_ID_OEN: 2000000, 2323: 600},  # OEN
        "AdGroup": {
            settings.HARDCODED_ACCOUNT_ID_INPOWERED_1: 1000,
            settings.HARDCODED_ACCOUNT_ID_INPOWERED_2: 1000,
            settings.HARDCODED_ACCOUNT_ID_INPOWERED_3: 1000,
            settings.HARDCODED_ACCOUNT_ID_BUSINESSWIRE: 10000,
        },  # inPowered  # inPowered  # inPowered  # Businesswire
        "ContentAd": {
            63: 10000,  # Allstate
            80: 10000,  # Dusan Test Account
            115: 10000,  # Luka's Test Account
            settings.HARDCODED_ACCOUNT_ID_BUSINESSWIRE: 10000,
            settings.HARDCODED_ACCOUNT_ID_OEN: 100000,
            950: 20000,  # MatchesFashion
        },
        "PublisherGroup": {settings.HARDCODED_ACCOUNT_ID_OEN: 2000000},  # OEN
        "BudgetLineItem": {settings.HARDCODED_ACCOUNT_ID_OEN: 1000},  # OEN
        "ConversionPixel": {4300: 25},  # GroupM/MAIF
    },
)


class EntityLimitExceeded(PermissionDenied):
    pass


def enforce(queryset, account_id=None, create_count=1):
    entity = queryset.model.__name__
    limit = ACCOUNT_EXCEPTIONS[entity].get(account_id, DEFAULT_LIMITS[entity])
    if queryset.count() + create_count > limit:
        raise EntityLimitExceeded
