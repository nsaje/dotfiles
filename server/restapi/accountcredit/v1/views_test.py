import datetime

from django.urls import reverse

import dash.constants
import dash.models
import utils.test_helper
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AccountCreditViewSetTest(RESTAPITest):
    def setUp(self):
        super().setUp()
        utils.test_helper.remove_permissions(self.user, ["can_view_platform_cost_breakdown"])

    @classmethod
    def credit_repr(
        cls,
        id=123,
        createdOn=datetime.datetime.now(),
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        total="500",
        allocated="200.0",
        available="300.0",
        license_fee=None,
        status=dash.constants.CreditLineItemStatus.SIGNED,
        currency=dash.constants.Currency.USD,
    ):
        resp = {
            "id": id,
            "createdOn": createdOn,
            "startDate": startDate,
            "endDate": endDate,
            "total": total,
            "allocated": allocated,
            "available": available,
            "status": dash.constants.CreditLineItemStatus.get_name(status),
            "currency": currency,
        }
        if license_fee is not None:
            resp["licenseFee"] = license_fee
        return cls.normalize(resp)

    def validate_against_db(self, credit, with_license_fee=False):
        credit_db = dash.models.CreditLineItem.objects.get(pk=credit["id"])
        license_fee = credit_db.license_fee if with_license_fee else None
        expected = self.credit_repr(
            id=str(credit_db.id),
            createdOn=credit_db.created_dt.date(),
            startDate=credit_db.start_date,
            endDate=credit_db.end_date,
            total=credit_db.effective_amount(),
            allocated=credit_db.get_allocated_amount(),
            available=credit_db.effective_amount() - credit_db.get_allocated_amount(),
            license_fee=license_fee,
            status=credit_db.status,
            currency=credit_db.currency,
        )
        self.assertEqual(expected, credit)

    def test_account_credits_get(self):
        r = self.client.get(
            reverse("restapi.accountcredit.v1:accounts_credits_details", kwargs={"account_id": 186, "credit_id": 861})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_account_credits_get_credit_doesnt_exist(self):
        r = self.client.get(
            reverse("restapi.accountcredit.v1:accounts_credits_details", kwargs={"account_id": 186, "credit_id": 1234})
        )
        self.assertResponseError(r, "DoesNotExist")

    def test_account_credits_get_account_doesnt_exist(self):
        r = self.client.get(
            reverse("restapi.accountcredit.v1:accounts_credits_details", kwargs={"account_id": 123, "credit_id": 861})
        )
        self.assertResponseError(r, "MissingDataError")

    def test_account_credits_list(self):
        r = self.client.get(reverse("restapi.accountcredit.v1:accounts_credits_list", kwargs={"account_id": 186}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_account_credits_pagination(self):
        account = magic_mixer.blend(dash.models.Account, users=[self.user])
        magic_mixer.cycle(10).blend(dash.models.CreditLineItem, account=account, end_date=datetime.date.today())
        r = self.client.get(
            reverse("restapi.accountcredit.v1:accounts_credits_list", kwargs={"account_id": account.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        marker_id = int(resp_json["data"][5]["id"]) - 1
        r_paginated = self.client.get(
            reverse("restapi.accountcredit.v1:accounts_credits_list", kwargs={"account_id": account.id}),
            {"limit": 2, "marker": marker_id},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    def test_license_fee_permissioned(self):
        utils.test_helper.add_permissions(self.user, ["can_view_platform_cost_breakdown"])
        r = self.client.get(
            reverse("restapi.accountcredit.v1:accounts_credits_details", kwargs={"account_id": 186, "credit_id": 861})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"], with_license_fee=True)
