import datetime
import decimal

import mock
from django.urls import reverse

import core.models
import dash.models
from dash import constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CampaignBudgetViewSetTest(RESTAPITestCase):
    @classmethod
    def budget_repr(
        cls,
        id=None,
        creditId=None,
        amount="500.0000",
        margin="0.1500",
        comment="mycomment",
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        state=constants.BudgetLineItemState.ACTIVE,
        spend="200.0000",
        available="300.0000",
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "creditId": str(creditId) if creditId is not None else None,
            "amount": str(amount),
            "margin": str(margin),
            "comment": str(comment) if comment is not None else "",
            "startDate": startDate,
            "endDate": endDate,
            "state": constants.BudgetLineItemState.get_name(state),
            "spend": spend,
            "available": available,
        }
        return cls.normalize(representation)

    def validate_against_db(self, budget, can_see_margin=True):
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
            margin=budget_db.margin,
            comment=budget_db.comment,
        )
        if not can_see_margin:
            del expected["margin"]
        self.assertEqual(expected, budget)

    def test_campaigns_budgets_get(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.AGENCY_SPEND_MARGIN])
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100,
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.v1:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_campaigns_budgets_get_no_permission(self):
        account = magic_mixer.blend(dash.models.Account)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100,
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.v1:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_campaigns_budgets_get_invalid(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.AGENCY_SPEND_MARGIN])
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.v1:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": 1234},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_campaigns_budgets_get_limited(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100,
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.v1:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"], can_see_margin=False)

        fields = resp_json["data"].keys()
        self.assertTrue("margin" not in fields)

    def test_campaigns_budgets_put(self):
        agency = self.mix_agency(
            self.user,
            permissions=[Permission.READ, Permission.WRITE, Permission.BUDGET, Permission.AGENCY_SPEND_MARGIN],
        )
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100,
        )

        r = self.client.put(
            reverse(
                "restapi.campaignbudget.v1:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            ),
            data={"creditId": str(credit.id), "amount": "900"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["amount"], "900")

    @mock.patch("utils.dates_helper.local_today", lambda: datetime.datetime(2016, 1, 15).date())
    def test_campaigns_budgets_list(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.AGENCY_SPEND_MARGIN], agency=agency
        )
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        magic_mixer.cycle(10).blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100,
        )

        r = self.client.get(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_campaigns_budgets_post(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[Permission.READ, Permission.WRITE, Permission.BUDGET, Permission.AGENCY_SPEND_MARGIN],
            agency=agency,
        )
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["amount"], test_budget["amount"])
        self.assertEqual(resp_json["data"]["startDate"], test_budget["startDate"])
        self.assertEqual(resp_json["data"]["endDate"], test_budget["endDate"])
        self.assertEqual(resp_json["data"]["margin"], test_budget["margin"])

    def test_campaigns_budgets_post_invalid(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )

        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "MissingDataError")

    def test_campaigns_budgets_post_no_budget_permission(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )

        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertEqual(r.status_code, 401)
        self.assertResponseError(r, "AuthorizationError")

    def test_campaigns_budgets_post_validation(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[Permission.READ, Permission.WRITE, Permission.BUDGET, Permission.AGENCY_SPEND_MARGIN],
            agency=agency,
        )
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        test_budget = self.budget_repr()
        del test_budget["creditId"]
        del test_budget["amount"]
        del test_budget["startDate"]
        del test_budget["endDate"]
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(creditId=credit.id)
        del test_budget["amount"]
        del test_budget["startDate"]
        del test_budget["endDate"]
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(creditId=credit.id, amount=decimal.Decimal("500.0000"))
        del test_budget["startDate"]
        del test_budget["endDate"]
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500.0000"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
        )
        del test_budget["endDate"]
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500"),
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["amount"], test_budget["amount"])
        self.assertEqual(resp_json["data"]["startDate"], test_budget["startDate"])
        self.assertEqual(resp_json["data"]["endDate"], test_budget["endDate"])

        test_end_date = datetime.date.today() - datetime.timedelta(days=9)
        r = self.client.put(
            reverse(
                "restapi.campaignbudget.v1:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": resp_json["data"]["id"]},
            ),
            data={"endDate": test_end_date},
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_campaigns_budgets_post_time_validation(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[Permission.READ, Permission.WRITE, Permission.BUDGET, Permission.AGENCY_SPEND_MARGIN],
            agency=agency,
        )
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500.0000"),
            startDate=datetime.date.today() - datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_budget = self.budget_repr(
            creditId=credit.id,
            amount=decimal.Decimal("500.0000"),
            startDate=datetime.date.today() - datetime.timedelta(days=2),
            endDate=datetime.date.today() - datetime.timedelta(days=1),
        )
        r = self.client.post(
            reverse("restapi.campaignbudget.v1:campaign_budgets_list", kwargs={"campaign_id": campaign.id}),
            data=test_budget,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
