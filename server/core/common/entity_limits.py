from collections import defaultdict

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
}

ACCOUNT_EXCEPTIONS = defaultdict(
    dict,
    {
        "Campaign": {305: 2000000},  # OEN
        "AdGroup": {490: 1000, 512: 1000, 513: 1000, 293: 10000},  # inPowered  # inPowered  # inPowered  # Businesswire
        "ContentAd": {
            63: 10000,  # Allstate
            80: 10000,  # Dusan Test Account
            115: 10000,  # Luka's Test Account
            293: 10000,  # Businesswire
            305: 100000,  # OEN
            950: 20000,  # MatchesFashion
        },
        "PublisherGroup": {305: 2000000},  # OEN
        "BudgetLineItem": {305: 1000},  # OEN
    },
)


class EntityLimitExceeded(PermissionDenied):
    pass


def enforce(queryset, account_id=None, create_count=1):
    entity = queryset.model.__name__
    limit = ACCOUNT_EXCEPTIONS[entity].get(account_id, DEFAULT_LIMITS[entity])
    if queryset.count() + create_count > limit:
        raise EntityLimitExceeded
