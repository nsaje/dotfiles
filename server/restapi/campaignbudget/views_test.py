from restapi.common.views_base_test import RESTAPITest
from django.urls import reverse

import dash.models
from dash import constants

import mock
import datetime
import decimal


class CampaignBudgetsTest(RESTAPITest):
    @classmethod
    def budget_repr(
        cls,
        id=1,
        creditId=1,
        amount="500.0000",
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        state=constants.BudgetLineItemState.ACTIVE,
        spend="200.0000",
        available="300.0000",
    ):
        representation = {
            "id": str(id),
            "creditId": str(creditId),
            "amount": str(amount),
            "startDate": startDate,
            "endDate": endDate,
            "state": constants.BudgetLineItemState.get_name(state),
            "spend": spend,
            "available": available,
        }
        return cls.normalize(representation)

    def validate_against_db(self, budget):
        budget_db = dash.models.BudgetLineItem.objects.get(pk=budget["id"])
        spend = budget_db.get_spend_data()["etf_total"]
        allocated = budget_db.allocated_amount()
        expected = self.budget_repr(
            id=budget_db.id,
            creditId=budget_db.credit.id,
            amount=decimal.Decimal(budget_db.amount),
            startDate=budget_db.start_date,
            endDate=budget_db.end_date,
            state=budget_db.state(),
            spend=spend,
            available=allocated,
        )
        self.assertEqual(expected, budget)

    def test_campaigns_budgets_get(self):
        r = self.client.get(reverse("campaign_budgets_details", kwargs={"campaign_id": 608, "budget_id": 1910}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_campaigns_budgets_get_invalid(self):
        r = self.client.get(reverse("campaign_budgets_details", kwargs={"campaign_id": 608, "budget_id": 1234}))
        self.assertResponseError(r, "MissingDataError")

    def test_campaigns_budgets_put(self):
        r = self.client.put(
            reverse("campaign_budgets_details", kwargs={"campaign_id": 608, "budget_id": 1910}),
            data={"amount": "900"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["amount"], "900")

    @mock.patch("dash.forms.dates_helper.local_today", lambda: datetime.datetime(2016, 1, 15).date())
    def test_campaigns_budgets_list(self):
        r = self.client.get(reverse("campaign_budgets_list", kwargs={"campaign_id": 608}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_campaigns_budgets_post(self):
        test_budget = self.budget_repr(
            id=1,
            creditId=861,
            amount=decimal.Decimal("500"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["amount"], test_budget["amount"])
        self.assertEqual(resp_json["data"]["startDate"], test_budget["startDate"])
        self.assertEqual(resp_json["data"]["endDate"], test_budget["endDate"])

    def test_campaigns_budgets_validation(self):
        test_budget = self.budget_repr(id=1)
        del test_budget["creditId"]
        del test_budget["amount"]
        del test_budget["startDate"]
        del test_budget["endDate"]
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(id=1, creditId=861)
        del test_budget["amount"]
        del test_budget["startDate"]
        del test_budget["endDate"]
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(id=1, creditId=861, amount=decimal.Decimal("500.0000"))
        del test_budget["startDate"]
        del test_budget["endDate"]
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(
            id=1,
            creditId=861,
            amount=decimal.Decimal("500.0000"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
        )
        del test_budget["endDate"]
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(
            id=1,
            creditId=861,
            amount=decimal.Decimal("500"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["amount"], test_budget["amount"])
        self.assertEqual(resp_json["data"]["startDate"], test_budget["startDate"])
        self.assertEqual(resp_json["data"]["endDate"], test_budget["endDate"])

        test_end_date = datetime.date.today() - datetime.timedelta(days=9)
        r = self.client.put(
            reverse("campaign_budgets_details", kwargs={"campaign_id": 608, "budget_id": 1910}),
            data={"endDate": test_end_date},
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_campaigns_budgets_time_validation(self):
        test_budget = self.budget_repr(
            id=1,
            creditId=861,
            amount=decimal.Decimal("500.0000"),
            startDate=datetime.date.today() - datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(
            id=1,
            creditId=861,
            amount=decimal.Decimal("500.0000"),
            startDate=datetime.date.today() - datetime.timedelta(days=2),
            endDate=datetime.date.today() - datetime.timedelta(days=1),
        )
        r = self.client.post(
            reverse("campaign_budgets_list", kwargs={"campaign_id": 608}), data=test_budget, format="json"
        )
        self.assertResponseError(r, "ValidationError")
