import datetime

from django.urls import reverse

import dash.constants
import dash.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class CampaignBudgetViewSetTest(RESTAPITest):
    def test_get(self):
        agency = magic_mixer.blend(dash.models.Agency)
        account = magic_mixer.blend(dash.models.Account, agency=agency, users=[self.user])
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
            amount=100000,
        )

        r = self.client.get(
            reverse(
                "restapi.campaignbudget.internal:campaign_budgets_details",
                kwargs={"campaign_id": campaign.id, "budget_id": budget.id},
            )
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["canEditStartDate"], budget.can_edit_start_date())
        self.assertEqual(resp_json["data"]["canEditEndDate"], budget.can_edit_end_date())
        self.assertEqual(resp_json["data"]["canEditAmount"], budget.can_edit_amount())
        self.assertEqual(resp_json["data"]["createdBy"], str(budget.created_by))
        self.assertEqual(resp_json["data"]["createdDt"], self.normalize(budget.created_dt))
        self.assertEqual(resp_json["data"]["licenseFee"], self.normalize(budget.credit.license_fee))
