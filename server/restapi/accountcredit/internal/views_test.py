import datetime

from django.urls import reverse

import dash.constants
import dash.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AccountCreditViewSetTest(RESTAPITest):
    def test_get(self):
        agency = magic_mixer.blend(dash.models.Agency)
        account = magic_mixer.blend(dash.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(
            reverse(
                "restapi.accountcredit.internal:accounts_credits_details",
                kwargs={"account_id": account.id, "credit_id": credit.id},
            )
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["comment"], credit.comment)
        self.assertEqual(resp_json["data"]["isAvailable"], credit.is_available())
        self.assertEqual(resp_json["data"]["isAgency"], credit.is_agency())
