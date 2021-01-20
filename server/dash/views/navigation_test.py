# -*- coding: utf-8 -*-
import datetime
import json

from django.urls import reverse
from mock import patch

from dash import constants
from dash import models
from utils import test_helper
from utils.base_test_case import BaseTestCase
from zemauth.models import User


def _configure_datetime_utcnow_mock(mock_datetime, utcnow_value):
    class DatetimeMock(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return utcnow_value

    mock_datetime.datetime = DatetimeMock
    mock_datetime.timedelta = datetime.timedelta


class NavigationAllAccountsDataViewTestCase(BaseTestCase):
    fixtures = ["test_navigation.yaml"]

    def _get(self, user_id, filtered_sources=None):
        username = User.objects.get(pk=user_id).email
        self.client.login(username=username, password="secret")

        response = self.client.get(reverse("navigation_all_accounts"), data={"filtered_sources": filtered_sources})

        response = json.loads(response.content)
        return response["data"]

    def test_get(self):
        response = self._get(1)
        self.assertDictEqual(response, {"accounts_count": 1, "default_account_id": 1})

        response = self._get(2)
        self.assertDictEqual(response, {"accounts_count": 1, "default_account_id": 2})

    def test_get_no_accounts(self):
        response = self._get(4)
        self.assertDictEqual(response, {"accounts_count": 0})

    def test_get_many_accounts(self):
        response = self._get(5)
        self.assertDictEqual(response, {"accounts_count": 3, "default_account_id": 2})

    def test_get_filtered_sources(self):
        response = self._get(1, [3])
        self.assertDictEqual(response, {"accounts_count": 0})


class NavigationDataViewTestCase(BaseTestCase):
    fixtures = ["test_navigation.yaml"]

    def setUp(self):
        super().setUp()
        self.mock_today = datetime.date(2016, 1, 2)

    def _get(self, user_id, level, obj_id, filtered_sources=None, filtered_agencies=None, filtered_account_types=None):
        username = User.objects.get(pk=user_id).email
        self.client.login(username=username, password="secret")

        response = self.client.get(
            reverse("navigation", kwargs={"level_": level, "id_": obj_id}), data={"filtered_sources": filtered_sources}
        )

        response = json.loads(response.content)
        return response["data"]

    def test_get_account(self):
        response = self._get(1, "accounts", 1)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": False,
                    "id": 1,
                    "name": "test account 1",
                    "agencyId": 1,
                    "agency": "Test Agency",
                    "currency": constants.Currency.USD,
                }
            },
        )

        # archived entity
        response = self._get(3, "accounts", 3)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": True,
                    "id": 3,
                    "name": "test account 3",
                    "agencyId": None,
                    "agency": None,
                    "currency": constants.Currency.USD,
                }
            },
        )

    def test_get_account_no_access(self):
        # has other accounts available
        response = self._get(1, "accounts", 2)
        self.assertDictEqual(response, {"message": "Account does not exist", "error_code": "MissingDataError"})

        # has no accounts available
        response = self._get(4, "accounts", 2)
        self.assertDictEqual(response, {"message": "Account does not exist", "error_code": "MissingDataError"})

    def test_get_campaign(self):
        response = self._get(1, "campaigns", 1)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": False,
                    "id": 1,
                    "name": "test account 1",
                    "agencyId": 1,
                    "agency": "Test Agency",
                    "currency": constants.Currency.USD,
                },
                "campaign": {
                    "archived": False,
                    "id": 1,
                    "name": "test campaign 1",
                    "type": constants.CampaignType.CONTENT,
                },
            },
        )

        # archived entity
        response = self._get(3, "campaigns", 3)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": True,
                    "id": 3,
                    "name": "test account 3",
                    "agencyId": None,
                    "agency": None,
                    "currency": constants.Currency.USD,
                },
                "campaign": {
                    "archived": True,
                    "id": 3,
                    "name": "test campaign 3",
                    "type": constants.CampaignType.CONTENT,
                },
            },
        )

    def test_get_campaign_no_access(self):
        # has other campaigns available
        response = self._get(1, "campaigns", 2)
        self.assertDictEqual(response, {"message": "Campaign does not exist", "error_code": "MissingDataError"})

        # has no campaigns available
        response = self._get(4, "campaigns", 2)
        self.assertDictEqual(response, {"message": "Campaign does not exist", "error_code": "MissingDataError"})

    @patch("utils.dates_helper.datetime")
    def test_get_ad_group(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(1, "ad_groups", 1)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": False,
                    "id": 1,
                    "name": "test account 1",
                    "agencyId": 1,
                    "agency": "Test Agency",
                    "currency": constants.Currency.USD,
                },
                "campaign": {
                    "archived": False,
                    "id": 1,
                    "name": "test campaign 1",
                    "type": constants.CampaignType.CONTENT,
                },
                "ad_group": {
                    "archived": False,
                    "id": 1,
                    "name": "test adgroup 1",
                    "state": 1,
                    "status": 1,
                    "autopilot_state": 2,
                    "active": "active",
                    "bidding_type": 1,
                },
            },
        )

        response = self._get(2, "ad_groups", 4)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": False,
                    "id": 2,
                    "name": "test account 2",
                    "agencyId": None,
                    "agency": None,
                    "currency": constants.Currency.USD,
                },
                "campaign": {
                    "archived": False,
                    "id": 2,
                    "name": "test campaign 2",
                    "type": constants.CampaignType.CONTENT,
                },
                "ad_group": {
                    "archived": True,
                    "id": 4,
                    "name": "test adgroup 4",
                    "state": 2,
                    "status": 2,
                    "autopilot_state": 2,
                    "active": "stopped",
                    "bidding_type": 2,
                },
            },
        )

    def test_get_ad_group_no_access(self):
        # has other available
        response = self._get(1, "ad_groups", 4)
        self.assertDictEqual(response, {"message": "Ad Group does not exist", "error_code": "MissingDataError"})

        # has nothing available
        response = self._get(4, "ad_groups", 2)
        self.assertDictEqual(response, {"message": "Ad Group does not exist", "error_code": "MissingDataError"})

    def test_get_account_filter(self):
        response = self._get(1, "accounts", 1)
        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": False,
                    "id": 1,
                    "name": "test account 1",
                    "agencyId": 1,
                    "agency": "Test Agency",
                    "currency": constants.Currency.USD,
                }
            },
        )

        # archived entity
        response = self._get(3, "accounts", 3)

        self.assertDictEqual(
            response,
            {
                "account": {
                    "archived": True,
                    "id": 3,
                    "name": "test account 3",
                    "agencyId": None,
                    "agency": None,
                    "currency": constants.Currency.USD,
                }
            },
        )


class NavigationTreeViewTestCase(BaseTestCase):
    fixtures = ["test_navigation.yaml"]

    def setUp(self):
        super().setUp()
        self.mock_today = datetime.date(2016, 1, 2)
        self.expected_response = [
            {
                "archived": False,
                "campaigns": [
                    {
                        "adGroups": [
                            {
                                "archived": False,
                                "id": 1,
                                "name": "test adgroup 1",
                                "state": 1,
                                "status": 1,
                                "autopilot_state": 2,
                                "active": "active",
                                "bidding_type": 1,
                            },
                            {
                                "archived": False,
                                "id": 2,
                                "name": "test adgroup 2",
                                "state": 1,
                                "status": 2,  # past dates
                                "autopilot_state": 2,
                                "active": "inactive",
                                "bidding_type": 1,
                            },
                            {
                                "archived": False,
                                "id": 3,
                                "name": "test adgroup 3",
                                "state": 2,
                                "status": 2,
                                "autopilot_state": 2,
                                "active": "stopped",
                                "bidding_type": 2,
                            },
                        ],
                        "archived": False,
                        "id": 1,
                        "name": "test campaign 1",
                        "type": constants.CampaignType.CONTENT,
                    }
                ],
                "id": 1,
                "agencyId": 1,
                "agency": "Test Agency",
                "currency": constants.Currency.USD,
                "name": "test account 1",
            }
        ]

    def _get(self, user_id, **kwargs):
        username = User.objects.get(pk=user_id).email
        self.client.login(username=username, password="secret")

        response = self.client.get(reverse("navigation_tree"), data=kwargs)

        response = json.loads(response.content)
        return response

    @patch("utils.dates_helper.datetime")
    def test_get(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(1)
        self.assertCountEqual(response["data"], self.expected_response)

    @patch("utils.dates_helper.datetime")
    def test_get_no_statuses(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(1, loadStatuses="false")
        self.assertCountEqual(
            [
                {
                    "campaigns": [
                        {
                            "adGroups": [
                                {"id": 1, "name": "test adgroup 1", "bidding_type": 1},
                                {"id": 2, "name": "test adgroup 2", "bidding_type": 1},
                                {"id": 3, "name": "test adgroup 3", "bidding_type": 2},
                            ],
                            "id": 1,
                            "name": "test campaign 1",
                            "type": constants.CampaignType.CONTENT,
                        }
                    ],
                    "id": 1,
                    "agencyId": 1,
                    "agency": "Test Agency",
                    "currency": constants.Currency.USD,
                    "name": "test account 1",
                }
            ],
            response["data"],
        )

    @patch("utils.dates_helper.datetime")
    def test_get_filtered_sources(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(1, filtered_sources=[2])
        expected_response = [
            {
                "archived": False,
                "campaigns": [
                    {
                        "adGroups": [
                            {
                                "archived": False,
                                "id": 1,
                                "name": "test adgroup 1",
                                "state": 1,
                                "status": 1,
                                "autopilot_state": 2,
                                "active": "active",
                                "bidding_type": 1,
                            },
                            {
                                "archived": False,
                                "id": 2,
                                "name": "test adgroup 2",
                                "state": 1,
                                "status": 2,
                                "autopilot_state": 2,
                                "active": "inactive",
                                "bidding_type": 1,
                            },
                            {
                                "archived": False,
                                "id": 3,
                                "name": "test adgroup 3",
                                "state": 2,
                                "status": 2,
                                "autopilot_state": 2,
                                "active": "stopped",
                                "bidding_type": 2,
                            },
                        ],
                        "archived": False,
                        "id": 1,
                        "name": "test campaign 1",
                        "type": constants.CampaignType.CONTENT,
                    }
                ],
                "id": 1,
                "agencyId": 1,
                "agency": "Test Agency",
                "currency": constants.Currency.USD,
                "name": "test account 1",
            }
        ]
        self.assertCountEqual(response["data"], expected_response)

    @patch("utils.dates_helper.datetime")
    def test_get_archived_ad_group_excluded(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(2)

        expected_response = [
            {
                "campaigns": [
                    {
                        "adGroups": [],
                        "id": 2,
                        "name": "test campaign 2",
                        "archived": False,
                        "type": constants.CampaignType.CONTENT,
                    }
                ],
                "id": 2,
                "name": "test account 2",
                "archived": False,
                "agencyId": None,
                "agency": None,
                "currency": constants.Currency.USD,
            }
        ]
        self.assertCountEqual(response["data"], expected_response)

    @patch("utils.dates_helper.datetime")
    def test_get_archived_campaign_excluded(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(7)

        expected_response = [
            {
                "campaigns": [],
                "id": 4,
                "name": "test account 4",
                "archived": False,
                "agencyId": None,
                "agency": None,
                "currency": constants.Currency.USD,
            }
        ]
        self.assertCountEqual(response["data"], expected_response)

    @patch("utils.dates_helper.datetime")
    def test_get_archived_account_excluded(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        response = self._get(3)

        expected_response = {"success": True}
        self.assertCountEqual(response, expected_response)

    def test_get_no_data(self):
        self.assertDictEqual(self._get(4), {"success": True})

    @patch("utils.dates_helper.datetime")
    def test_get_account_filter_agency(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )
        user = User.objects.get(pk=1)

        account = models.Account.objects.get(pk=1)
        response = self._get(1)
        self.assertCountEqual(response["data"], self.expected_response)

        agency = models.Agency.objects.get(pk=1)

        agency2 = models.Agency(name="Test 2")
        agency2.save(test_helper.fake_request(user))

        account.agency = agency
        account.save(test_helper.fake_request(user))

        response = self._get(1, filtered_agencies=[agency2.id])
        self.assertCountEqual({"success": True}, response)

        response = self._get(1, filtered_agencies=[agency.id])
        self.assertCountEqual(self.expected_response, response["data"])

        response = self._get(1, filtered_agencies=[agency2.id, agency.id])
        self.assertCountEqual(self.expected_response, response["data"])

    @patch("utils.dates_helper.datetime")
    def test_get_account_type_filter(self, mock_datetime):
        _configure_datetime_utcnow_mock(
            mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day)
        )

        response = self._get(1)
        self.assertCountEqual(self.expected_response, response["data"])

        response = self._get(1, filtered_account_types=[constants.AccountType.MANAGED])
        self.assertCountEqual({"success": True}, response)

        response = self._get(1, filtered_account_types=[constants.AccountType.UNKNOWN])
        self.assertCountEqual(self.expected_response, response["data"])
