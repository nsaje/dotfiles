import datetime
import decimal

from django.urls import reverse

import dash.constants
import dash.models
import dash.views.helpers
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CampaignBudgetViewSetTest(RESTAPITestCase):
    def test_get(self):
        agency = self.mix_agency(
            self.user,
            permissions=[
                Permission.READ,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
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
            service_fee=decimal.Decimal("0.1"),
        )
        budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100000,
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.internal:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            )
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(budget.id))
        self.assertEqual(resp_json["data"]["canEditStartDate"], budget.can_edit_start_date())
        self.assertEqual(resp_json["data"]["canEditEndDate"], budget.can_edit_end_date())
        self.assertEqual(resp_json["data"]["canEditAmount"], budget.can_edit_amount())
        self.assertEqual(resp_json["data"]["createdBy"], str(budget.created_by))
        self.assertEqual(resp_json["data"]["createdDt"], self.normalize(budget.created_dt))
        self.assertIsNotNone(resp_json["data"]["margin"])
        self.assertEqual(
            resp_json["data"]["licenseFee"], dash.views.helpers.format_decimal_to_percent(budget.credit.license_fee)
        )
        self.assertEqual(
            resp_json["data"]["serviceFee"], dash.views.helpers.format_decimal_to_percent(budget.credit.service_fee)
        )

    def test_get_limited(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
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
            service_fee=decimal.Decimal("0.1"),
        )
        budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(20),
            created_by=self.user,
            amount=100000,
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.internal:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            )
        )
        resp_json = self.assertResponseValid(r)

        fields = resp_json["data"].keys()
        self.assertEqual(resp_json["data"]["id"], str(budget.id))
        self.assertTrue("margin" not in fields)
        self.assertTrue("licenseFee" not in fields)
        self.assertTrue("serviceFee" not in fields)
