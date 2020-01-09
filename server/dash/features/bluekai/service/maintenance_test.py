from django.test import TestCase
from mixer.backend.django import mixer
from mock import ANY
from mock import patch

from dash.features.bluekai import constants
from dash.features.bluekai import models

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
        # FIXME: uncomment when reenabling adding categories
        # mock_category_create.assert_called_once_with(
        #     category_id=TEST_TAXONOMY[1]["id"],
        #     parent_category_id=TEST_TAXONOMY[1]["parentCategory"]["id"],
        #     name=TEST_TAXONOMY[1]["name"],
        #     description=TEST_TAXONOMY[1]["description"],
        #     reach=TEST_TAXONOMY[1]["stats"]["reach"],
        #     price=TEST_TAXONOMY[1]["categoryPrice"],
        #     navigation_only=TEST_TAXONOMY[1]["isForNavigationOnlyFlag"],
        # )
        self.assertFalse(mock_category_create.called)
        mock_category_update.assert_called_once_with(
            ANY,
            name=TEST_TAXONOMY[0]["name"],
            description=TEST_TAXONOMY[0]["description"],
            reach=TEST_TAXONOMY[0]["stats"]["reach"],
            price=TEST_TAXONOMY[0]["categoryPrice"],
            navigation_only=TEST_TAXONOMY[0]["isForNavigationOnlyFlag"],
        )


class AddCategoryTestCase(TestCase):

    test_audience = {
        "name": "Test Audience",
        "prospecting": True,
        "retargeting": False,
        "segments": {"AND": [{"AND": [{"OR": [{"cat": 1234, "freq": [1, None]}]}]}]},
    }

    @patch("dash.features.bluekai.service.bluekaiapi.update_audience")
    @patch("dash.features.bluekai.service.bluekaiapi.get_audience")
    def test_add_category(self, mock_get_audience, mock_update_audience):
        mock_get_audience.return_value = self.test_audience
        maintenance.add_category_to_audience(4321)
        mock_update_audience.assert_called_with(
            maintenance.AUDIENCE_ID,
            {
                "name": "Test Audience",
                "prospecting": True,
                "retargeting": False,
                "segments": {
                    "AND": [{"AND": [{"OR": [{"cat": 1234, "freq": [1, None]}, {"cat": 4321, "freq": [1, None]}]}]}]
                },
            },
        )

    @patch("dash.features.bluekai.service.bluekaiapi.update_audience")
    @patch("dash.features.bluekai.service.bluekaiapi.get_audience")
    def test_add_existing_category(self, mock_get_audience, mock_update_audience):
        mock_get_audience.return_value = self.test_audience
        maintenance.add_category_to_audience(1234)
        self.assertFalse(mock_update_audience.called)
