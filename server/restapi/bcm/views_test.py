#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mock import patch
import datetime
from decimal import Decimal
from dash import history_helpers

from django.urls import reverse
from django.test import TestCase

from zemauth.models import User
from dash import models, constants
from utils.test_helper import fake_request
from django.test.client import RequestFactory

import automation.campaignstop
from utils import converters
from utils import test_helper


class BCMViewTestCase(TestCase):
    fixtures = ["test_bcm.yaml", "test_agency.yaml"]

    def setUp(self):
        self.maxDiff = None
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        for account in models.Account.objects.all():
            account.users.add(self.user)

        self.client.login(username=self.user.email, password="secret")


class AccountCreditViewTest(BCMViewTestCase):
    def test_permissions(self):
        url = reverse("accounts_credit", kwargs={"account_id": 1})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url, json.dumps({"cancel": 1}), content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        url = reverse("accounts_credit", kwargs={"account_id": 1})
        c = models.CreditLineItem.objects.get(pk=1)
        c.status = constants.CreditLineItemStatus.SIGNED
        c.save()

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["data"],
            {
                "active": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "created_on": "2014-06-04",
                        "created_by": "ziga.stopinsek@zemanta.com",
                        "license_fee": "20%",
                        "flat_fee": "0.0",
                        "allocated": "100000.0000",
                        "total": "100000.0000",
                        "comment": "Test case",
                        "id": 1,
                        "is_signed": True,
                        "is_canceled": False,
                        "is_agency": False,
                        "budgets": [{"amount": 100000, "id": 1}],
                        "start_date": "2015-10-01",
                        "salesforce_url": None,
                    }
                ],
                "past": [],
                "totals": {
                    "available": "0.0000",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "past": "0",
                    "currency": constants.Currency.USD,
                },
            },
        )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2016, 11, 11)
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            json.loads(response.content)["data"],
            {
                "active": [],
                "past": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "created_on": "2014-06-04",
                        "created_by": "ziga.stopinsek@zemanta.com",
                        "license_fee": "20%",
                        "flat_fee": "0.0",
                        "comment": "Test case",
                        "allocated": "100000.0000",
                        "total": "100000.0000",
                        "id": 1,
                        "is_signed": True,
                        "is_canceled": False,
                        "is_agency": False,
                        "budgets": [{"amount": 100000, "id": 1}],
                        "start_date": "2015-10-01",
                        "salesforce_url": None,
                    }
                ],
                "totals": {
                    "available": "0.0000",
                    "allocated": "0",
                    "past": "100000.0000",
                    "total": "100000.0000",
                    "currency": constants.Currency.USD,
                },
            },
        )

    def test_get_as_agency(self):
        url = reverse("accounts_credit", kwargs={"account_id": 1000})
        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["data"],
            {
                "active": [
                    {
                        "available": "99900.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "created_on": "2014-06-04",
                        "created_by": "agency-master@test.com",
                        "license_fee": "20%",
                        "flat_fee": "100.0000",
                        "allocated": "0",
                        "total": "99900.0000",
                        "comment": "Agency credit",
                        "id": 1000,
                        "is_signed": True,
                        "is_canceled": False,
                        "is_agency": True,
                        "budgets": [],
                        "salesforce_url": None,
                        "start_date": "2015-10-01",
                    }
                ],
                "past": [],
                "totals": {
                    "available": "99900.0000",
                    "allocated": "0",
                    "total": "99900.0000",
                    "past": "0",
                    "currency": constants.Currency.USD,
                },
            },
        )

    def test_post(self):
        url = reverse("accounts_credit", kwargs={"account_id": 1})

        credit = models.CreditLineItem.objects.create_unsafe(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=10000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        self.assertEqual(
            models.CreditLineItem.objects.filter(status=constants.CreditLineItemStatus.CANCELED).count(), 0
        )
        request_data = {"cancel": [credit.pk]}

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, json.dumps(request_data), content_type="application/json")
        response_data = json.loads(response.content)
        self.assertTrue(credit.pk in response_data["data"]["canceled"])
        self.assertEqual(
            models.CreditLineItem.objects.filter(status=constants.CreditLineItemStatus.CANCELED).count(), 1
        )

    def test_put_empty(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment="TESTCASE_PUT")))
        url = reverse("accounts_credit", kwargs={"account_id": 1})

        request_data = {}

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data))

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertTrue("amount" in response_data["data"]["errors"])
        self.assertTrue("start_date" in response_data["data"]["errors"])
        self.assertTrue("end_date" in response_data["data"]["errors"])
        self.assertTrue("license_fee" in response_data["data"]["errors"])

    def test_put_invalid_start_date(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment="TESTCASE_PUT")))

        url = reverse("accounts_credit", kwargs={"account_id": 1})

        request_data = {
            "start_date": "2015-11-10",
            "end_date": "2015-11-20",
            "amount": "5000",
            "license_fee": "20%",
            "comment": "TESTCASE_PUT",
        }

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse("amount" in response_data["data"]["errors"])
        self.assertTrue("start_date" in response_data["data"]["errors"])
        self.assertFalse("end_date" in response_data["data"]["errors"])
        self.assertFalse("license_fee" in response_data["data"]["errors"])

    def test_put_valid(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment="TESTCASE_PUT")))

        url = reverse("accounts_credit", kwargs={"account_id": 1})
        request_data = {
            "start_date": "2015-11-11",
            "end_date": "2015-11-20",
            "amount": "5000",
            "license_fee": "20%",
            "comment": "TESTCASE_PUT",
        }

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        item_id = response_data["data"]

        item = models.CreditLineItem.objects.get(comment="TESTCASE_PUT")
        self.assertEqual(item.pk, item_id)
        self.assertEqual(item.account_id, 1)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(self.user, hist.created_by)
        self.assertEqual(constants.HistoryActionType.CREATE, hist.action_type)

    def test_put_agency_empty(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment="TESTCASE_PUT")))

        url = reverse("accounts_credit", kwargs={"account_id": 1000})

        request_data = {}

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data))

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertTrue("amount" in response_data["data"]["errors"])
        self.assertTrue("start_date" in response_data["data"]["errors"])
        self.assertTrue("end_date" in response_data["data"]["errors"])
        self.assertTrue("license_fee" in response_data["data"]["errors"])

    def test_put_agency_invalid_start_date(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment="TESTCASE_PUT")))

        url = reverse("accounts_credit", kwargs={"account_id": 1000})

        request_data = {
            "start_date": "2015-11-10",
            "end_date": "2015-11-20",
            "amount": "5000",
            "license_fee": "20%",
            "comment": "TESTCASE_PUT",
            "is_agency": True,
        }

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data), content_type="application/json")

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse("amount" in response_data["data"]["errors"])
        self.assertTrue("start_date" in response_data["data"]["errors"])
        self.assertFalse("end_date" in response_data["data"]["errors"])
        self.assertFalse("license_fee" in response_data["data"]["errors"])

    def test_put_agency_valid(self):
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(comment="TESTCASE_PUT")))

        url = reverse("accounts_credit", kwargs={"account_id": 1000})

        request_data = {
            "start_date": "2015-11-11",
            "end_date": "2015-11-20",
            "amount": "5000",
            "license_fee": "20%",
            "comment": "TESTCASE_PUT",
            "is_agency": True,
        }

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.put(url, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        item_id = response_data["data"]

        item = models.CreditLineItem.objects.get(comment="TESTCASE_PUT")
        self.assertEqual(item.pk, item_id)
        self.assertEqual(item.agency_id, 1)

        hist = history_helpers.get_agency_history(models.Agency.objects.get(pk=1)).first()
        self.assertEqual(self.user, hist.created_by)
        self.assertEqual(constants.HistoryActionType.CREATE, hist.action_type)


class AccountCreditItemViewTest(BCMViewTestCase):
    def test_permissions(self):
        url = reverse("accounts_credit_item", kwargs={"account_id": 1, "credit_id": 1})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))
        response = self.client.delete(url)
        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))
        self.assertEqual(response.status_code, 401)

        response = self.client.post(url, json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_get(self):
        url = reverse("accounts_credit_item", kwargs={"account_id": 1, "credit_id": 1})

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)

        response_item = json.loads(response.content)["data"]
        self.assertEqual(
            response_item,
            {
                "comment": "Test case",
                "account_id": 1,
                "start_date": "2015-10-01",
                "end_date": "2015-11-30",
                "currency": constants.Currency.USD,
                "created_on": "2014-06-04",
                "created_by": "ziga.stopinsek@zemanta.com",
                "license_fee": "20%",
                "id": 1,
                "is_signed": False,
                "is_canceled": False,
                "is_agency": False,
                "amount": 100000,
                "budgets": [
                    {
                        "campaign": "test campaign 1",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "spend": "0.0000",
                        "id": 1,
                        "total": "100000.0000",
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "salesforce_url": None,
                "contract_id": None,
                "contract_number": None,
            },
        )

    def test_delete(self):
        url = reverse("accounts_credit_item", kwargs={"account_id": 3, "credit_id": 2})

        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))

        test_helper.add_permissions(self.user, ["account_credit_view"])

        url = reverse("accounts_credit_item", kwargs={"account_id": 3, "credit_id": 2})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(pk=2)))

    def test_post(self):
        url = reverse("accounts_credit_item", kwargs={"account_id": 3, "credit_id": 2})

        data = {}
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, 401)

        test_helper.add_permissions(self.user, ["account_credit_view"])

        item = models.CreditLineItem.objects.get(pk=2)
        self.assertEqual(item.amount, 100000)

        data = {
            "start_date": "2015-12-01",
            "end_date": "2015-12-01",
            "amount": "1000",
            "license_fee": "30%",
            "currency": constants.Currency.EUR,
            "comment": "no comment",
            "account": 3,
        }
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, json.dumps(data), content_type="application/json")

        item = models.CreditLineItem.objects.get(pk=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(item.amount, 1000)
        self.assertEqual(item.currency, constants.Currency.EUR)
        self.assertEqual(json.loads(response.content)["data"], "2")
        self.assertEqual(item.account_id, 3)

        hist = models.History.objects.order_by("-created_dt").first()
        self.assertEqual(self.user, hist.created_by)
        self.assertEqual(item.account, hist.account)
        self.assertEqual(constants.HistoryActionType.CREDIT_CHANGE, hist.action_type)

    def test_get_agency(self):
        agency = models.Agency.objects.get(pk=1)
        account = models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(fake_request(User.objects.get(pk=1)))

        credit = models.CreditLineItem.objects.get(pk=1)
        credit.account = None
        credit.agency = agency
        credit.save()

        url = reverse("accounts_credit_item", kwargs={"account_id": 1, "credit_id": 1})

        test_helper.add_permissions(self.user, ["account_credit_view"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)

        response_item = response.json()["data"]
        self.assertEqual(
            response_item,
            {
                "comment": "Test case",
                "account_id": 1,
                "start_date": "2015-10-01",
                "end_date": "2015-11-30",
                "currency": constants.Currency.USD,
                "created_on": "2014-06-04",
                "created_by": "ziga.stopinsek@zemanta.com",
                "license_fee": "20%",
                "id": 1,
                "is_signed": False,
                "is_canceled": False,
                "is_agency": True,
                "amount": 100000,
                "budgets": [
                    {
                        "campaign": "test campaign 1",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "spend": "0.0000",
                        "id": 1,
                        "total": "100000.0000",
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "salesforce_url": None,
                "contract_id": None,
                "contract_number": None,
            },
        )

    def test_delete_agency(self):
        agency = models.Agency.objects.get(pk=1)
        account = models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(fake_request(User.objects.get(pk=1)))

        credit = models.CreditLineItem.objects.get(pk=1)
        credit.account = None
        credit.agency = agency
        credit.save()

        url = reverse("accounts_credit_item", kwargs={"account_id": 3, "credit_id": 2})

        self.assertEqual(1, len(models.CreditLineItem.objects.filter(pk=2)))

        test_helper.add_permissions(self.user, ["account_credit_view"])

        url = reverse("accounts_credit_item", kwargs={"account_id": 3, "credit_id": 2})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, len(models.CreditLineItem.objects.filter(pk=2)))

    def test_post_agency(self):
        url = reverse("accounts_credit_item", kwargs={"account_id": 1000, "credit_id": 1000})

        data = {}
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, data)

        self.assertEqual(response.status_code, 401)

        test_helper.add_permissions(self.user, ["account_credit_view"])

        item = models.CreditLineItem.objects.get(pk=1000)
        self.assertEqual(item.amount, 100000)

        data = {
            "start_date": str(item.start_date),
            "end_date": str(item.end_date),
            "amount": "2000000",
            "license_fee": "20%",
            "currency": constants.Currency.EUR,
            "comment": "no comment",
            "account": 1000,
            "is_agency": True,
        }
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.post(url, json.dumps(data), content_type="application/json")

        item = models.CreditLineItem.objects.get(pk=1000)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(item.amount, 2000000)
        self.assertEqual(item.currency, constants.Currency.EUR)
        self.assertEqual(json.loads(response.content)["data"], "1000")
        self.assertEqual(item.agency_id, 1)

        hist = models.History.objects.order_by("-created_dt").first()
        self.assertEqual(self.user, hist.created_by)
        self.assertEqual(item.agency, hist.agency)
        self.assertEqual(constants.HistoryActionType.CREDIT_CHANGE, hist.action_type)


class CampaignBudgetViewTest(BCMViewTestCase):
    def setUp(self):
        super(CampaignBudgetViewTest, self).setUp()

    def test_get(self):
        url = reverse("campaigns_budget", kwargs={"campaign_id": 1})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)["data"]

        self.maxDiff = None

        self.assertEqual(
            data,
            {
                "active": [
                    {
                        "credit": 1,
                        "available": "100000.0000",
                        "is_editable": False,
                        "is_updatable": True,
                        "state": 1,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "license_fee": "20%",
                        "total": "100000.0000",
                        "spend": "0.0000",
                        "id": 1,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "past": [],
                "credits": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "id": 1,
                        "is_available": False,
                        "comment": "Test case",
                        "license_fee": "20",
                        "total": "100000.0000",
                        "start_date": "2015-10-01",
                        "is_agency": False,
                    }
                ],
                "totals": {
                    "current": {"available": "100000.0000", "past": "0.0000", "unallocated": "0.0000"},
                    "lifetime": {
                        "data_spend": "0.0000",
                        "campaign_spend": "0.0000",
                        "media_spend": "0.0000",
                        "license_fee": "0.0000",
                    },
                    "currency": constants.Currency.USD,
                },
            },
        )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 11)
            response = self.client.get(url)

        data = json.loads(response.content)["data"]
        self.assertEqual(
            data,
            {
                "active": [
                    {
                        "credit": 1,
                        "available": "100000.0000",
                        "is_editable": True,
                        "is_updatable": False,
                        "state": 2,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "license_fee": "20%",
                        "total": "100000.0000",
                        "spend": "0.0000",
                        "id": 1,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "past": [],
                "credits": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "id": 1,
                        "is_available": False,
                        "comment": "Test case",
                        "license_fee": "20",
                        "total": "100000.0000",
                        "start_date": "2015-10-01",
                        "is_agency": False,
                    }
                ],
                "totals": {
                    "current": {"available": "100000.0000", "past": "0.0000", "unallocated": "0.0000"},
                    "lifetime": {
                        "data_spend": "0.0000",
                        "campaign_spend": "0.0000",
                        "media_spend": "0.0000",
                        "license_fee": "0.0000",
                    },
                    "currency": constants.Currency.USD,
                },
            },
        )

    def test_get_bcm_v2(self):
        account = models.Account.objects.get(id=1)
        account.set_uses_bcm_v2(None, True)

        url = reverse("campaigns_budget", kwargs={"campaign_id": 1})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)["data"]

        self.assertEqual(
            data,
            {
                "active": [
                    {
                        "credit": 1,
                        "available": "100000.0000",
                        "is_editable": False,
                        "is_updatable": True,
                        "state": 1,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "total": "100000.0000",
                        "spend": "0.0000",
                        "id": 1,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "past": [],
                "credits": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "id": 1,
                        "is_available": False,
                        "comment": "Test case",
                        "total": "100000.0000",
                        "start_date": "2015-10-01",
                        "is_agency": False,
                    }
                ],
                "totals": {
                    "current": {"available": "100000.0000", "past": "0.0000", "unallocated": "0.0000"},
                    "lifetime": {"campaign_spend": "0.0000"},
                    "currency": constants.Currency.USD,
                },
            },
        )

        test_helper.add_permissions(self.user, ["can_view_platform_cost_breakdown"])
        test_helper.add_permissions(self.user, ["can_view_agency_cost_breakdown"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)["data"]

        self.assertEqual(
            data,
            {
                "active": [
                    {
                        "credit": 1,
                        "available": "100000.0000",
                        "is_editable": False,
                        "is_updatable": True,
                        "state": 1,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "license_fee": "20%",
                        "margin": "15%",
                        "total": "100000.0000",
                        "spend": "0.0000",
                        "id": 1,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "past": [],
                "credits": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "id": 1,
                        "is_available": False,
                        "comment": "Test case",
                        "license_fee": "20",
                        "total": "100000.0000",
                        "start_date": "2015-10-01",
                        "is_agency": False,
                    }
                ],
                "totals": {
                    "current": {"available": "100000.0000", "past": "0.0000", "unallocated": "0.0000"},
                    "lifetime": {
                        "data_spend": "0.0000",
                        "campaign_spend": "0.0000",
                        "media_spend": "0.0000",
                        "license_fee": "0.0000",
                        "margin": "0.0000",
                    },
                    "currency": constants.Currency.USD,
                },
            },
        )

    def test_get_with_margin(self):
        url = reverse("campaigns_budget", kwargs={"campaign_id": 1})

        test_helper.add_permissions(self.user, ["can_view_agency_margin"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 11)
            response = self.client.get(url)

        data = json.loads(response.content)["data"]
        self.assertEqual(
            data,
            {
                "active": [
                    {
                        "credit": 1,
                        "available": "100000.0000",
                        "is_editable": True,
                        "is_updatable": False,
                        "state": 2,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "license_fee": "20%",
                        "margin": "15%",
                        "total": "100000.0000",
                        "spend": "0.0000",
                        "id": 1,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    }
                ],
                "past": [],
                "credits": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "id": 1,
                        "is_available": False,
                        "comment": "Test case",
                        "license_fee": "20",
                        "total": "100000.0000",
                        "start_date": "2015-10-01",
                        "is_agency": False,
                    }
                ],
                "totals": {
                    "current": {"available": "100000.0000", "past": "0.0000", "unallocated": "0.0000"},
                    "lifetime": {
                        "data_spend": "0.0000",
                        "campaign_spend": "0.0000",
                        "media_spend": "0.0000",
                        "license_fee": "0.0000",
                        "margin": "0.0000",
                    },
                    "currency": constants.Currency.USD,
                },
            },
        )

    def test_get_as_agency_manager(self):
        url = reverse("campaigns_budget", kwargs={"campaign_id": 1})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertCountEqual(
            data["credits"],
            [
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "currency": constants.Currency.USD,
                    "id": 1,
                    "is_available": False,
                    "comment": "Test case",
                    "license_fee": "20",
                    "total": "100000.0000",
                    "start_date": "2015-10-01",
                    "is_agency": False,
                }
            ],
        )

        r = RequestFactory().get("")
        r.user = User.objects.get(pk=1)

        account = models.Account.objects.get(pk=1)
        account.agency = models.Agency.objects.get(pk=1)
        account.save(r)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertCountEqual(
            data["credits"],
            [
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "currency": constants.Currency.USD,
                    "id": 1,
                    "is_available": False,
                    "comment": "Test case",
                    "license_fee": "20",
                    "total": "100000.0000",
                    "start_date": "2015-10-01",
                    "is_agency": False,
                },
                {
                    "available": "99900.0000",
                    "comment": "Agency credit",
                    "end_date": "2015-11-30",
                    "start_date": "2015-10-01",
                    "currency": constants.Currency.USD,
                    "is_available": True,
                    "license_fee": "20",
                    "total": "99900.0000",
                    "id": 1000,
                    "is_agency": True,
                },
            ],
        )

    def test_put(self):
        c = models.CreditLineItem.objects.create_unsafe(
            account_id=10,
            start_date=datetime.date(2015, 10, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=10000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )

        data = {
            "credit": c.pk,
            "amount": "1000",
            "start_date": "2015-10-01",
            "end_date": "2015-12-31",
            "comment": "Comment",
        }

        url = reverse("campaigns_budget", kwargs={"campaign_id": 10})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        data["start_date"] = "2015-12-01"
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        credit = models.CreditLineItem.objects.get(pk=c.pk)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        hist = history_helpers.get_campaign_history(models.Campaign.objects.get(pk=10)).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.CREATE, hist.action_type)

        insert_id = int(json.loads(response.content)["data"])
        self.assertEqual(models.BudgetLineItem.objects.get(pk=insert_id).comment, "Comment")

        hist = models.History.objects.filter(level=constants.HistoryLevel.CAMPAIGN).order_by("-created_dt").first()
        self.assertEqual(self.user, hist.created_by)

    def test_put_margin_no_permission(self):
        c = models.CreditLineItem.objects.create_unsafe(
            account_id=10,
            start_date=datetime.date(2017, 10, 1),
            end_date=datetime.date(2017, 11, 30),
            amount=10000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )

        data = {
            "credit": c.pk,
            "amount": "1000",
            "start_date": "2017-10-01",
            "end_date": "2017-10-31",
            "margin": "20%",
            "comment": "Comment",
        }
        models.CreditLineItem.objects.filter(pk=c.pk).update(status=constants.CreditLineItemStatus.SIGNED)

        campaign = models.Campaign.objects.get(pk=10)
        campaign.account.uses_bcm_v2 = True  # in non-bcm-v2 this permission is public
        campaign.account.save(None)

        url = reverse("campaigns_budget", kwargs={"campaign_id": campaign.id})
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        insert_id = int(json.loads(response.content)["data"])
        self.assertEqual(
            models.BudgetLineItem.objects.get(pk=insert_id).margin,
            models.BudgetLineItem._meta.get_field("margin").default,
        )

    def test_put_margin(self):
        c = models.CreditLineItem.objects.create_unsafe(
            account_id=10,
            start_date=datetime.date(2015, 10, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=10000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.PENDING,
            created_by_id=1,
        )

        data = {
            "credit": c.pk,
            "amount": "1000",
            "start_date": "2015-10-01",
            "end_date": "2015-10-31",
            "margin": "20%",
            "comment": "Comment",
        }
        models.CreditLineItem.objects.filter(pk=c.pk).update(status=constants.CreditLineItemStatus.SIGNED)

        test_helper.add_permissions(self.user, ["can_manage_agency_margin"])
        url = reverse("campaigns_budget", kwargs={"campaign_id": 10})
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        insert_id = int(json.loads(response.content)["data"])
        self.assertEqual(models.BudgetLineItem.objects.get(pk=insert_id).margin, Decimal("0.2"))


class CampaignBudgetItemViewTest(BCMViewTestCase):
    def test_get(self):
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["data"],
            {
                "id": 1,
                "comment": "Test case",
                "is_editable": False,
                "is_updatable": True,
                "amount": 100000,
                "end_date": "2015-11-30",
                "state": 1,
                "currency": constants.Currency.USD,
                "created_at": "2014-06-04T05:58:21",
                "credit": {
                    "license_fee": "0.2000",
                    "id": 1,
                    "name": "1 - test account 1 - $100000 - from 2015-10-01 to 2015-11-30",
                },
                "start_date": "2015-10-01",
                "created_by": "ziga.stopinsek@zemanta.com",
                "spend": "0.0000",
                "available": "100000.0000",
            },
        )

    def test_get_not_authorized(self):
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 10})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_with_margin(self):
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})

        test_helper.add_permissions(self.user, ["can_view_agency_margin"])

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 11)
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["data"],
            {
                "id": 1,
                "comment": "Test case",
                "is_editable": False,
                "is_updatable": True,
                "amount": 100000,
                "end_date": "2015-11-30",
                "margin": "15%",
                "state": 1,
                "currency": constants.Currency.USD,
                "created_at": "2014-06-04T05:58:21",
                "credit": {
                    "license_fee": "0.2000",
                    "id": 1,
                    "name": "1 - test account 1 - $100000 - from 2015-10-01 to 2015-11-30",
                },
                "start_date": "2015-10-01",
                "created_by": "ziga.stopinsek@zemanta.com",
                "spend": "0.0000",
                "available": "100000.0000",
            },
        )

    def test_post(self):
        data = {}
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        data = {
            "credit": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "amount": 1000,
            "comment": "Test case test_post",
        }
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)

        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["data"], {"id": 1})
        self.assertEqual(models.BudgetLineItem.objects.get(pk=1).comment, "Test case test_post")

        hist = history_helpers.get_campaign_history(models.Campaign.objects.get(pk=1)).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.BUDGET_CHANGE, hist.action_type)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["data"], {"id": 1})

        hist = models.History.objects.filter(level=constants.HistoryLevel.CAMPAIGN).order_by("-created_dt").first()
        self.assertEqual(self.user, hist.created_by)

    def test_post_margin(self):
        data = {}
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})

        data = {
            "credit": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "margin": "50%",
            "amount": 1000,
            "comment": "Test case test_post",
        }

        campaign = models.Campaign.objects.get(pk=1)
        campaign.account.uses_bcm_v2 = True
        campaign.account.save(None)

        models.CreditLineItem.objects.filter(id=1).update(status=constants.CreditLineItemStatus.SIGNED)
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["data"], {"id": 1})
        self.assertEqual(models.BudgetLineItem.objects.get(id=1).margin, Decimal("0.15"))  # no change

    @patch("automation.campaignstop.validate_minimum_budget_amount")
    def test_post_lower_unactive(self, mock_validate_min_amount):
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})
        data = {
            "credit": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "amount": 90000,
            "comment": "Test case test_post",
        }
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)  # before start date
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertTrue(mock_validate_min_amount.called)
        self.assertEqual(response.status_code, 200)

    @patch("automation.campaignstop.validate_minimum_budget_amount")
    def test_post_lower_campaign_stop_off(self, mock_validate_min_amount):
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        campaign = models.Campaign.objects.get(id=1)
        campaign.real_time_campaign_stop = False
        campaign.save()

        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})
        data = {
            "credit": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "amount": 90000,
            "comment": "Test case test_post",
        }
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)  # before start date
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        response_data = json.loads(response.content)

        self.assertTrue("amount" in response_data["data"]["errors"])
        self.assertEqual(
            response_data["data"]["errors"]["amount"], ["If campaign stop is disabled amount cannot be lowered."]
        )
        self.assertFalse(mock_validate_min_amount.called)
        self.assertEqual(response.status_code, 400)

    @patch("automation.campaignstop.validate_minimum_budget_amount")
    def test_post_lower_active(self, mock_validate_min_amount):
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})
        data = {
            "credit": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "amount": 90000,
            "comment": "Test case test_post",
        }

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertTrue(mock_validate_min_amount.called)
        self.assertEqual(response.status_code, 200)

    @patch("automation.campaignstop.validate_minimum_budget_amount")
    def test_post_lower_active_too_low(self, mock_validate_min_amount):
        credit = models.CreditLineItem.objects.get(pk=1)
        credit.status = 1
        credit.end_date = datetime.date(2015, 12, 31)
        credit.save()

        mock_validate_min_amount.side_effect = automation.campaignstop.CampaignStopValidationException(
            "msg", min_amount=95000
        )
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})
        data = {
            "credit": 1,
            "start_date": "2015-10-01",
            "end_date": "2015-11-30",
            "amount": 90000,
            "comment": "Test case test_post",
        }

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 10, 30)
            response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertTrue(mock_validate_min_amount.called)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["data"]["errors"]["amount"], ["Budget amount has to be at least $95000.00."])

    def test_delete(self):
        url = reverse("campaigns_budget_item", kwargs={"campaign_id": 1, "budget_id": 1})

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2016, 1, 1)
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 9, 30)
            response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)


class BudgetSpendInViewsTestCase(BCMViewTestCase):
    def test_active_budget(self):
        today = datetime.date(2015, 11, 11)

        budget = models.BudgetLineItem.objects.get(pk=1)
        budget.credit.amount = 250000
        budget.credit.status = constants.CreditLineItemStatus.SIGNED
        budget.credit.save()
        models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=today,
            media_spend_nano=300 * converters.CURRENCY_TO_NANO,
            data_spend_nano=200 * converters.CURRENCY_TO_NANO,
            license_fee_nano=50 * converters.CURRENCY_TO_NANO,
            margin_nano=55 * converters.CURRENCY_TO_NANO,
        )

        # Another budget with daily statement
        budget.pk = None
        budget.total = 50000
        budget.save()
        models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=today,
            media_spend_nano=100 * converters.CURRENCY_TO_NANO,
            data_spend_nano=100 * converters.CURRENCY_TO_NANO,
            license_fee_nano=105 * (10 ** 8),
            margin_nano=Decimal("21.05") * converters.CURRENCY_TO_NANO,
        )

        url = reverse("campaigns_budget", kwargs={"campaign_id": 1})

        test_helper.add_permissions(self.user, ["can_view_agency_margin"])
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = today
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)["data"]

        self.assertEqual(
            data,
            {
                "active": [
                    {
                        "credit": 1,
                        "available": "99789.5000",
                        "is_editable": False,
                        "is_updatable": True,
                        "state": 1,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "license_fee": "20%",
                        "margin": "15%",
                        "total": "100000.0000",
                        "spend": "210.5000",
                        "id": 11,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    },
                    {
                        "credit": 1,
                        "available": "99450.0000",
                        "is_editable": False,
                        "is_updatable": True,
                        "state": 1,
                        "currency": constants.Currency.USD,
                        "end_date": "2015-11-30",
                        "license_fee": "20%",
                        "margin": "15%",
                        "total": "100000.0000",
                        "spend": "550.0000",
                        "id": 1,
                        "comment": "Test case",
                        "start_date": "2015-10-01",
                    },
                ],
                "past": [],
                "credits": [
                    {
                        "available": "50000.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "id": 1,
                        "is_available": True,
                        "license_fee": "20",
                        "comment": "Test case",
                        "total": "250000.0000",
                        "start_date": "2015-10-01",
                        "is_agency": False,
                    }
                ],
                "totals": {
                    "current": {"available": "199239.5000", "past": "0.0000", "unallocated": "50000.0000"},
                    "lifetime": {
                        "data_spend": "300.0000",
                        "campaign_spend": "760.5000",
                        "media_spend": "400.0000",
                        "license_fee": "60.5000",
                        "margin": "76.0500",
                    },
                    "currency": constants.Currency.USD,
                },
            },
        )


class BudgetReserveInViewsTestCase(BCMViewTestCase):
    def test_credit_view(self):
        url = reverse("accounts_credit", kwargs={"account_id": 1})
        today = datetime.date(2015, 11, 11)

        test_helper.add_permissions(self.user, ["account_credit_view"])

        credit = models.CreditLineItem.objects.create_unsafe(
            account_id=1,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 30),
            amount=10000,
            license_fee=Decimal("0.2"),
            status=constants.CreditLineItemStatus.SIGNED,
            created_by_id=1,
        )
        budget = models.BudgetLineItem.objects.create_unsafe(
            credit=credit,
            amount=10000,
            start_date=datetime.date(2015, 11, 1),
            end_date=datetime.date(2015, 11, 10),
            campaign_id=1,
        )

        models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=today - datetime.timedelta(1),
            media_spend_nano=500 * converters.CURRENCY_TO_NANO,
            data_spend_nano=0,
            license_fee_nano=50 * converters.CURRENCY_TO_NANO,
            margin_nano=0,
        )
        for num in range(0, 5):
            models.BudgetDailyStatement.objects.create(
                budget=budget,
                date=today + datetime.timedelta(num),
                media_spend_nano=800 * converters.CURRENCY_TO_NANO,
                data_spend_nano=0,
                license_fee_nano=80 * converters.CURRENCY_TO_NANO,
                margin_nano=0,
            )

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = today
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json()["data"],
            {
                "active": [
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "created_on": str(budget.created_dt.date()),
                        "created_by": "ziga.stopinsek@zemanta.com",
                        "license_fee": "20%",
                        "flat_fee": "0.0",
                        "allocated": "10000.0000",
                        "total": "10000.0000",
                        "id": 1001,
                        "is_signed": True,
                        "is_canceled": False,
                        "is_agency": False,
                        "comment": None,
                        "budgets": [{"amount": 10000, "id": 11}],
                        "start_date": "2015-11-01",
                        "salesforce_url": None,
                    },
                    {
                        "available": "0.0000",
                        "end_date": "2015-11-30",
                        "currency": constants.Currency.USD,
                        "created_on": "2014-06-04",
                        "created_by": "ziga.stopinsek@zemanta.com",
                        "license_fee": "20%",
                        "flat_fee": "0.0",
                        "allocated": "100000.0000",
                        "comment": "Test case",
                        "total": "100000.0000",
                        "id": 1,
                        "is_signed": False,
                        "is_canceled": False,
                        "is_agency": False,
                        "budgets": [{"amount": 100000, "id": 1}],
                        "start_date": "2015-10-01",
                        "salesforce_url": None,
                    },
                ],
                "past": [],
                "totals": {
                    "available": "0.0000",
                    "allocated": "10000.0000",
                    "total": "10000.0000",
                    "past": "0",
                    "currency": constants.Currency.USD,
                },
            },
        )

        on_reserve_data = {
            "active": [
                {
                    "available": "5006.0000",
                    "end_date": "2015-11-30",
                    "currency": constants.Currency.USD,
                    "created_on": str(budget.created_dt.date()),
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "flat_fee": "0.0",
                    "comment": None,
                    "allocated": "4994.0000",
                    "total": "10000.0000",
                    "id": 1001,
                    "is_signed": True,
                    "is_canceled": False,
                    "is_agency": False,
                    "budgets": [{"amount": 10000, "id": 11}],
                    "start_date": "2015-11-01",
                    "salesforce_url": None,
                },
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "currency": constants.Currency.USD,
                    "comment": "Test case",
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "flat_fee": "0.0",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "is_agency": False,
                    "budgets": [{"amount": 100000, "id": 1}],
                    "start_date": "2015-10-01",
                    "salesforce_url": None,
                },
            ],
            "past": [],
            "totals": {
                "past": "0",
                "available": "5006.0000",
                "allocated": "4994.0000",
                "total": "10000.0000",
                "currency": constants.Currency.USD,
            },
        }
        on_freed_data = {
            "active": [
                {
                    "available": "5050.0000",
                    "end_date": "2015-11-30",
                    "currency": constants.Currency.USD,
                    "created_on": str(budget.created_dt.date()),
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "flat_fee": "0.0",
                    "allocated": "4950.0000",
                    "comment": None,
                    "total": "10000.0000",
                    "id": 1001,
                    "is_signed": True,
                    "is_canceled": False,
                    "is_agency": False,
                    "budgets": [{"amount": 10000, "id": 11}],
                    "start_date": "2015-11-01",
                    "salesforce_url": None,
                },
                {
                    "available": "0.0000",
                    "end_date": "2015-11-30",
                    "currency": constants.Currency.USD,
                    "created_on": "2014-06-04",
                    "created_by": "ziga.stopinsek@zemanta.com",
                    "license_fee": "20%",
                    "flat_fee": "0.0",
                    "comment": "Test case",
                    "allocated": "100000.0000",
                    "total": "100000.0000",
                    "id": 1,
                    "is_signed": False,
                    "is_canceled": False,
                    "is_agency": False,
                    "budgets": [{"amount": 100000, "id": 1}],
                    "start_date": "2015-10-01",
                    "salesforce_url": None,
                },
            ],
            "past": [],
            "totals": {
                "past": "0",
                "available": "5050.0000",
                "allocated": "4950.0000",
                "total": "10000.0000",
                "currency": constants.Currency.USD,
            },
        }

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 11)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)

        self.assertEqual(json.loads(response.content)["data"], on_reserve_data)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 12)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)["data"], on_reserve_data)

        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 13)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)["data"], on_reserve_data)

        # After sync time has passed
        with patch("utils.dates_helper.local_today") as mock_now:
            mock_now.return_value = datetime.date(2015, 11, 14)
            budget.free_inactive_allocated_assets()
            response = self.client.get(url)
        self.assertEqual(json.loads(response.content)["data"], on_freed_data)
