from django.test import TestCase
from mixer.backend.django import mixer
from mock import ANY
from mock import patch

import core.models
import dash.constants
import utils.dates_helper
from dash.features.bluekai import constants
from dash.features.bluekai import models
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import maintenance

TEST_TAXONOMY = [
    {
        "buyerPrice": -1.0,
        "categoryPrice": 1.0,
        "categoryType": "regular",
        "description": (
            "Oracle audiences consist of the highest quality "
            "inventory available across Oracle Data Cloud's global "
            "data assets. These audiences are inclusive of owned "
            "and curated inventory from AddThis, BlueKai and "
            "Datalogix and contain signal from both online and "
            "offline sources."
        ),
        "id": 671901,
        "isCountableFlag": True,
        "isExplicitPriceFloorFlag": False,
        "isForNavigationOnlyFlag": False,
        "isIncludeForAnalyticsFlag": True,
        "isLeafFlag": False,
        "isMutuallyExclusiveChildrenFlag": False,
        "isPublicFlag": True,
        "links": [],
        "name": "Oracle",
        "ownershipType": "thirdParty",
        "parentCategory": {"id": 344},
        "partner": {"id": 0},
        "pathFromRoot": {"ids": [344, 671901], "names": ["ROOT", "Oracle"]},
        "sortOrder": 2,
        "stats": {"reach": 4979629800},
        "status": "active",
        "universalPrice": 1.0,
        "vertical": {"name": "Private - Default"},
        "visibilityStatus": "notHidden",
    },
    {
        "buyerPrice": -1.0,
        "categoryPrice": 1.0,
        "categoryType": "regular",
        "description": (
            "Oracle Telecommunication audiences contain people "
            "interested and in-market as well as current "
            "subscribers for consumer telecommunication and data "
            "communication services from mobile carriers, cable "
            "companies and other internet service providers."
        ),
        "id": 840141,
        "isCountableFlag": True,
        "isExplicitPriceFloorFlag": False,
        "isForNavigationOnlyFlag": False,
        "isIncludeForAnalyticsFlag": True,
        "isLeafFlag": False,
        "isMutuallyExclusiveChildrenFlag": False,
        "isPublicFlag": True,
        "links": [],
        "name": "Telecommunications",
        "notes": "",
        "ownershipType": "thirdParty",
        "parentCategory": {"id": 671901},
        "partner": {"id": 0},
        "pathFromRoot": {"ids": [344, 671901, 840141], "names": ["ROOT", "Oracle", "Telecommunications"]},
        "sortOrder": 9999,
        "stats": {"reach": 436984800},
        "status": "active",
        "universalPrice": 1.0,
        "vertical": {"name": "Oracle - Telecommunications"},
        "visibilityStatus": "notHidden",
    },
]


class GetUpdatedCategoriesTestCase(TestCase):
    def setUp(self):
        existing_category = mixer.blend(
            models.BlueKaiCategory,
            category_id=671901,
            parent_category_id=344,
            navigation_only=False,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        self.existing_categories = {existing_category.category_id: existing_category}

    def test_get_updated_categories(self):
        new_categories, updated_categories = maintenance._get_updated_categories(
            TEST_TAXONOMY, self.existing_categories
        )
        self.assertEqual(1, len(new_categories))
        self.assertEqual(1, len(updated_categories))

        new_category = new_categories[0]
        updated_category = updated_categories[0]

        self.assertEqual(840141, new_category["category_id"])
        self.assertEqual(671901, new_category["parent_category_id"])
        self.assertEqual(TEST_TAXONOMY[1]["name"], new_category["name"])
        self.assertEqual(TEST_TAXONOMY[1]["description"], new_category["description"])
        self.assertEqual(TEST_TAXONOMY[1]["stats"]["reach"], new_category["reach"])
        self.assertEqual(TEST_TAXONOMY[1]["categoryPrice"], new_category["price"])
        self.assertEqual(False, new_category["navigation_only"])

        self.assertEqual(list(self.existing_categories.values())[0].id, updated_category["id"])
        self.assertEqual(671901, updated_category["category_id"])
        self.assertEqual(344, updated_category["parent_category_id"])
        self.assertEqual(TEST_TAXONOMY[0]["name"], updated_category["name"])
        self.assertEqual(TEST_TAXONOMY[0]["description"], updated_category["description"])
        self.assertEqual(TEST_TAXONOMY[0]["stats"]["reach"], updated_category["reach"])
        self.assertEqual(TEST_TAXONOMY[0]["categoryPrice"], updated_category["price"])
        self.assertEqual(False, updated_category["navigation_only"])


class RefreshBluekaiCategoriesTestCase(TestCase):
    def setUp(self):
        existing_category = mixer.blend(
            models.BlueKaiCategory,
            category_id=TEST_TAXONOMY[0]["id"],
            parent_category_id=TEST_TAXONOMY[0]["parentCategory"]["id"],
            navigation_only=False,
            status=constants.BlueKaiCategoryStatus.ACTIVE,
        )
        self.existing_categories = {existing_category.category_id: existing_category}

    @patch.object(models.BlueKaiCategory, "update", autospec=True)
    @patch("dash.features.bluekai.models.BlueKaiCategory.objects.create", autospec=True)
    @patch("dash.features.bluekai.service.maintenance._get_existing_categories", autospec=True)
    @patch("dash.features.bluekai.service.bluekaiapi.get_taxonomy", autospec=True)
    def test_refresh_bluekai_categories(
        self, mock_get_taxonomy, mock_get_existing, mock_category_create, mock_category_update
    ):
        mock_get_taxonomy.return_value = TEST_TAXONOMY
        mock_get_existing.return_value = self.existing_categories

        maintenance.refresh_bluekai_categories()
        mock_category_create.assert_called_once_with(
            category_id=TEST_TAXONOMY[1]["id"],
            parent_category_id=TEST_TAXONOMY[1]["parentCategory"]["id"],
            name=TEST_TAXONOMY[1]["name"],
            description=TEST_TAXONOMY[1]["description"],
            reach=TEST_TAXONOMY[1]["stats"]["reach"],
            price=TEST_TAXONOMY[1]["categoryPrice"],
            navigation_only=TEST_TAXONOMY[1]["isForNavigationOnlyFlag"],
        )
        mock_category_update.assert_called_once_with(
            ANY,
            name=TEST_TAXONOMY[0]["name"],
            description=TEST_TAXONOMY[0]["description"],
            reach=TEST_TAXONOMY[0]["stats"]["reach"],
            price=TEST_TAXONOMY[0]["categoryPrice"],
            navigation_only=TEST_TAXONOMY[0]["isForNavigationOnlyFlag"],
        )


class UpdateDynamicAudienceTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        self.ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group)
        for category in (111, 222, 333, 444, 555, 666):  # 777 should not be in to check filtering
            magic_mixer.blend(models.BlueKaiCategory, category_id=category)
        self.ad_group.settings.update_unsafe(
            None,
            archived=False,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            start_date=utils.dates_helper.local_yesterday(),
            end_date=utils.dates_helper.days_after(utils.dates_helper.local_today(), 5),
            bluekai_targeting=[
                "and",
                ["or", "bluekai:111", "bluekai:222", "bluekai:333", "bluekai:444", "category_888"],
                ["not", ["or", "bluekai:555", "bluekai:666", "bluekai:777", "category_999"]],
            ],
        )
        self.ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.active_ad_groups = core.models.AdGroup.objects.filter_running_and_has_budget().select_related("settings")

    @patch("dash.features.bluekai.service.bluekaiapi.update_audience")
    @patch("dash.features.bluekai.service.bluekaiapi.get_audience")
    def test_update_dynamic_audience(self, mock_get_audience, mock_update_audience):
        mock_get_audience.return_value = {
            "name": "Test Audience",
            "prospecting": True,
            "retargeting": False,
            "segments": {
                "AND": [{"AND": [{"OR": [{"cat": 1234, "freq": [1, None]}, {"cat": 4321, "freq": [1, None]}]}]}]
            },
        }
        maintenance.update_dynamic_audience()
        mock_update_audience.assert_called_with(
            maintenance.AUDIENCE_ID,
            {
                "name": "Test Audience",
                "prospecting": True,
                "retargeting": False,
                "recency": 500,
                "segments": {
                    "AND": [
                        {
                            "AND": [
                                {
                                    "OR": test_helper.ListMatcher(
                                        [
                                            {"cat": 111, "freq": [1, None]},
                                            {"cat": 222, "freq": [1, None]},
                                            {"cat": 333, "freq": [1, None]},
                                            {"cat": 444, "freq": [1, None]},
                                            {"cat": 555, "freq": [1, None]},
                                            {"cat": 666, "freq": [1, None]},
                                        ],
                                        key=lambda x: x["cat"],
                                    )
                                }
                            ]
                        }
                    ]
                },
            },
        )
