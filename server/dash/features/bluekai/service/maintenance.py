from django.conf import settings

import core.models
from dash.features.bluekai import models
from utils import zlogging

from . import bluekaiapi

logger = zlogging.getLogger(__name__)

RECENCY_ALL = 500

AUDIENCE_ID = 636435
CAMPAIGN_ID = 552848
STATUS_ACTIVE = "active"


def is_bluekai_campaign_running(campaign_id=CAMPAIGN_ID):
    bluekai_campaign = bluekaiapi.get_campaign(campaign_id)
    return bluekai_campaign["status"] == STATUS_ACTIVE, bluekai_campaign


def update_dynamic_audience():
    audience = bluekaiapi.get_audience(AUDIENCE_ID)
    segments_categories = []
    z1_categories = _get_ad_group_settings_for_bluekai()
    # only take categories from basic Oracle taxonomy. Other categories are synced by audiences created manually by CS
    z1_categories_filtered = models.BlueKaiCategory.objects.filter(category_id__in=z1_categories).values_list(
        "category_id", flat=True
    )
    for category in z1_categories_filtered:
        segments_categories.append({"cat": category, "freq": [1, None]})
    segments = {"AND": [{"AND": [{"OR": segments_categories}]}]}
    data = {
        "name": audience["name"],
        "prospecting": audience["prospecting"],
        "retargeting": audience["retargeting"],
        "recency": RECENCY_ALL,
        "segments": segments,
    }
    bluekaiapi.update_audience(AUDIENCE_ID, data)


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
        .exclude(campaign__account_id=settings.HARDCODED_ACCOUNT_ID_OEN)
        .exclude(settings__bluekai_targeting="")
        .exclude(settings__bluekai_targeting=[])
    )
    return {
        int(elem.partition(":")[2])
        for elem in flatten_bluekai_rule(
            [elem.settings.bluekai_targeting for elem in active_ad_groups if elem.settings.bluekai_targeting]
        )
    }


def refresh_bluekai_categories():
    taxonomy = bluekaiapi.get_taxonomy()
    existing_categories = _get_existing_categories()
    new_categories, updated_categories = _get_updated_categories(taxonomy, existing_categories)

    for category in new_categories:
        models.BlueKaiCategory.objects.create(**category)

    for category in updated_categories:
        existing_categories[category["category_id"]].update(
            name=category["name"],
            description=category["description"],
            reach=category["reach"],
            price=category["price"],
            navigation_only=category["navigation_only"],
        )


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
