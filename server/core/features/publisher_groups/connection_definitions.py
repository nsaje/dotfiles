from typing import Dict
from typing import Type
from typing import Union

from typing_extensions import TypedDict

from dash import models

Entity = Union[Type[models.Agency], Type[models.Account], Type[models.Campaign], Type[models.AdGroup]]


class ModelAttributeDict(TypedDict):
    model: Entity
    attribute: str


CONNECTION_TYPE_AGENCY_BLACKLIST = "agencyBlacklist"
CONNECTION_TYPE_AGENCY_WHITELIST = "agencyWhitelist"
CONNECTION_TYPE_ACCOUNT_BLACKLIST = "accountBlacklist"
CONNECTION_TYPE_ACCOUNT_WHITELIST = "accountWhitelist"
CONNECTION_TYPE_CAMPAIGN_BLACKLIST = "campaignBlacklist"
CONNECTION_TYPE_CAMPAIGN_WHITELIST = "campaignWhitelist"
CONNECTION_TYPE_AD_GROUP_BLACKLIST = "adGroupBlacklist"
CONNECTION_TYPE_AD_GROUP_WHITELIST = "adGroupWhitelist"

CONNECTION_TYPE_MAP: Dict[str, ModelAttributeDict] = {
    CONNECTION_TYPE_AGENCY_BLACKLIST: {"model": models.Agency, "attribute": "blacklist_publisher_groups"},
    CONNECTION_TYPE_AGENCY_WHITELIST: {"model": models.Agency, "attribute": "whitelist_publisher_groups"},
    CONNECTION_TYPE_ACCOUNT_BLACKLIST: {"model": models.Account, "attribute": "blacklist_publisher_groups"},
    CONNECTION_TYPE_ACCOUNT_WHITELIST: {"model": models.Account, "attribute": "whitelist_publisher_groups"},
    CONNECTION_TYPE_CAMPAIGN_BLACKLIST: {"model": models.Campaign, "attribute": "blacklist_publisher_groups"},
    CONNECTION_TYPE_CAMPAIGN_WHITELIST: {"model": models.Campaign, "attribute": "whitelist_publisher_groups"},
    CONNECTION_TYPE_AD_GROUP_BLACKLIST: {"model": models.AdGroup, "attribute": "blacklist_publisher_groups"},
    CONNECTION_TYPE_AD_GROUP_WHITELIST: {"model": models.AdGroup, "attribute": "whitelist_publisher_groups"},
}

CONNECTION_NAMES_MAP: Dict[str, str] = {
    CONNECTION_TYPE_AGENCY_BLACKLIST: "blacklisted in agency",
    CONNECTION_TYPE_AGENCY_WHITELIST: "whitelisted in agency",
    CONNECTION_TYPE_ACCOUNT_BLACKLIST: "blacklisted in account",
    CONNECTION_TYPE_ACCOUNT_WHITELIST: "whitelisted in account",
    CONNECTION_TYPE_CAMPAIGN_BLACKLIST: "blacklisted in campaign",
    CONNECTION_TYPE_CAMPAIGN_WHITELIST: "whitelisted in campaign",
    CONNECTION_TYPE_AD_GROUP_BLACKLIST: "blacklisted in ad group",
    CONNECTION_TYPE_AD_GROUP_WHITELIST: "whitelisted in ad group",
}


class InvalidConnectionType(Exception):
    pass
