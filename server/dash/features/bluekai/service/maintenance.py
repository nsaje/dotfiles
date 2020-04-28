import copy

import core.models
from dash.features.bluekai import models
from utils import zlogging

from . import bluekaiapi

logger = zlogging.getLogger(__name__)

RECENCY_ALL = 500
OEN_ACCOUNT_ID = 305
AUDIENCE_ID = 202305
CAMPAIGN_ID = 383218
NEW_AUDIENCE_ID = 549424
NEW_CAMPAIGN_ID = 456928
STATUS_ACTIVE = "active"


def is_bluekai_campaign_running(campaign_id=CAMPAIGN_ID):
    bluekai_campaign = bluekaiapi.get_campaign(campaign_id)
    return bluekai_campaign["status"] == STATUS_ACTIVE, bluekai_campaign


def refresh_bluekai_categories():
    taxonomy = bluekaiapi.get_taxonomy()
    existing_categories = _get_existing_categories()
    new_categories, updated_categories = _get_updated_categories(taxonomy, existing_categories)

    # FIXME: we're currently unable to extend audience in BK, so we shouldn't add new
    # ones because users can't access that traffic
    # for category in new_categories:
    #     models.BlueKaiCategory.objects.create(**category)

    for category in updated_categories:
        existing_categories[category["category_id"]].update(
            name=category["name"],
            description=category["description"],
            reach=category["reach"],
            price=category["price"],
            navigation_only=category["navigation_only"],
        )


def add_category_to_audience(category_id):
    audience = bluekaiapi.get_audience(AUDIENCE_ID)
    segments = copy.deepcopy(audience["segments"])

    found = False
    for category in segments["AND"][0]["AND"][0]["OR"]:
        if category_id == category["cat"]:
            found = True

        # update only with relevant fields
        for k in list(category.keys()):
            if k not in ["cat", "freq"]:
                del category[k]

    if not found:
        segments["AND"][0]["AND"][0]["OR"].append({"cat": category_id, "freq": [1, None]})
        data = {
            "name": audience["name"],
            "prospecting": audience["prospecting"],
            "retargeting": audience["retargeting"],
            "segments": segments,
        }
        bluekaiapi.update_audience(AUDIENCE_ID, data)


def cross_check_audience_categories():
    audience = bluekaiapi.get_audience(AUDIENCE_ID)
    active_categories = models.BlueKaiCategory.objects.active()

    messages = []
    segments = audience["segments"]
    if list(segments.keys()) != ["AND"]:
        messages.append("Operator AND expected on top level")
    elif len(segments["AND"]) != 1:
        messages.append("Top level AND has more than one child")
    elif list(segments["AND"][0].keys()) != ["AND"]:
        messages.append("Operator AND expected on second level")
    elif len(segments["AND"][0]["AND"]) != 1:
        messages.append("Second level AND has more than one child")
    elif list(segments["AND"][0]["AND"][0].keys()) != ["OR"]:
        messages.append("Operator OR expected on third level")
    else:
        audience_categories = set(item["cat"] for item in segments["AND"][0]["AND"][0]["OR"])
        for category in active_categories:
            if category.category_id not in audience_categories:
                messages.append(
                    "Category {} is active in the system but "
                    "isn't added to the audience".format(category.category_id)
                )

    if messages:
        messages = [
            "BlueKai campaign is out of sync with Z1. "
            "Check https://partner.bluekai.com/rails/campaigns/{}. "
            "Details:".format(CAMPAIGN_ID)
        ] + messages

    return "\n".join(messages)


def update_dynamic_audience():
    audience = bluekaiapi.get_audience(NEW_AUDIENCE_ID)
    segments_categories = []
    for category in _get_ad_group_settings_for_bluekai():
        segments_categories.append({"cat": int(category), "freq": [1, None]})
    segments = {"AND": [{"AND": [{"OR": segments_categories}]}]}
    data = {
        "name": audience["name"],
        "prospecting": audience["prospecting"],
        "retargeting": audience["retargeting"],
        "recency": RECENCY_ALL,
        "segments": segments,
    }
    bluekaiapi.update_audience(NEW_AUDIENCE_ID, data)


def _get_existing_categories():
    return {
        existing_category.category_id: existing_category for existing_category in models.BlueKaiCategory.objects.all()
    }


def _get_updated_categories(taxonomy, existing_categories):
    new_categories, updated_categories, number_of_incomplete_categories = [], [], 0
    for bluekai_category in taxonomy:
        if bluekai_category["status"] != STATUS_ACTIVE:
            logger.warning(
                "BlueKai category not active. id=%s status=%s", bluekai_category["id"], bluekai_category["status"]
            )
        if "description" not in bluekai_category:
            number_of_incomplete_categories += 1
            continue

        category = {
            "category_id": bluekai_category["id"],
            "parent_category_id": bluekai_category["parentCategory"]["id"],
            "name": bluekai_category["name"],
            "description": bluekai_category["description"],
            "reach": bluekai_category["stats"]["reach"],
            "price": bluekai_category["categoryPrice"],
            "navigation_only": bluekai_category["isForNavigationOnlyFlag"],
        }
        existing_category = existing_categories.get(bluekai_category["id"])
        if not existing_category:
            new_categories.append(category)
            continue

        category["id"] = existing_category.pk
        updated_categories.append(category)
    if number_of_incomplete_categories:
        logger.warning(f"number of incomplete bluekai_categories: {number_of_incomplete_categories}")

    return new_categories, updated_categories


def _get_ad_group_settings_for_bluekai():
    def flatten_bluekai_rule(bluekai_rule):
        return (
            [bluekai_rule]
            if not isinstance(bluekai_rule, list)
            else [
                category
                for categories in bluekai_rule
                for category in flatten_bluekai_rule(categories)
                if category.startswith("bluekai")
            ]
        )

    active_ad_groups = (
        core.models.AdGroup.objects.filter_running_and_has_budget()
        .select_related("settings")
        .exclude(campaign__account_id=OEN_ACCOUNT_ID)
        .exclude(settings__bluekai_targeting="")
        .exclude(settings__bluekai_targeting=[])
    )
    return {
        elem.partition(":")[2]
        for elem in flatten_bluekai_rule(
            [elem.settings.bluekai_targeting for elem in active_ad_groups if elem.settings.bluekai_targeting]
        )
    }
