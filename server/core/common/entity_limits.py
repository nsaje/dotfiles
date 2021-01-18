from collections import defaultdict

from django.conf import settings
from rest_framework.exceptions import PermissionDenied

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
    "BidModifier": 5000,
}

ACCOUNT_EXCEPTIONS = defaultdict(
    dict,
    {
        "Campaign": {settings.HARDCODED_ACCOUNT_ID_OEN: 5000000, 2323: 600, 5921: 5000},  # OEN  # ironsource
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
        "PublisherGroup": {settings.HARDCODED_ACCOUNT_ID_OEN: 5000000, 5921: 1000},  # ironsource
        "BudgetLineItem": {settings.HARDCODED_ACCOUNT_ID_OEN: 1000},  # OEN
        "ConversionPixel": {4300: 25},  # GroupM/MAIF
    },
)


class EntityLimitExceeded(PermissionDenied):
    def __init__(self, message=None, limit=None):
        super().__init__(message)
        self.limit = limit


def enforce(queryset, account_id=None, create_count=1):
    entity = queryset.model.__name__
    limit = ACCOUNT_EXCEPTIONS[entity].get(account_id, DEFAULT_LIMITS[entity])
    if queryset.count() + create_count > limit:
        raise EntityLimitExceeded(
            "You have reached the limit of {limit} active entities of type {entity}. Please archive some to be able to create more.".format(
                limit=limit, entity=entity
            ),
            limit=limit,
        )
