import datetime
import decimal

from django.urls import reverse

import core.models
import dash.constants
import dash.models
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CreditViewSetTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()

    @classmethod
    def credit_repr(
        cls,
        id=None,
        createdOn=datetime.datetime.now(),
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        total=None,
        allocated=None,
        available=None,
        service_fee=None,
        license_fee=None,
        status=dash.constants.CreditLineItemStatus.SIGNED,
        currency=dash.constants.Currency.USD,
    ):
        resp = {
            "id": str(id) if id is not None else None,
            "createdOn": createdOn,
            "startDate": startDate,
            "endDate": endDate,
            "total": total.quantize(decimal.Decimal(".1") ** 4, rounding=decimal.ROUND_HALF_DOWN)
            if total is not None
            else None,
            "allocated": allocated.quantize(decimal.Decimal(".1") ** 4, rounding=decimal.ROUND_HALF_DOWN)
            if allocated is not None
            else None,
            "available": available.quantize(decimal.Decimal(".1") ** 4, rounding=decimal.ROUND_HALF_DOWN)
            if available is not None
            else None,
            "status": dash.constants.CreditLineItemStatus.get_name(status),
            "currency": currency,
        }
        if service_fee is not None:
            resp["serviceFee"] = service_fee
        if license_fee is not None:
            resp["licenseFee"] = license_fee
        return cls.normalize(resp)

    def validate_against_db(self, credit, with_service_fee=False, with_license_fee=False):
        credit_db = dash.models.CreditLineItem.objects.get(pk=credit["id"])
        service_fee = credit_db.service_fee if with_service_fee else None
        license_fee = credit_db.license_fee if with_license_fee else None
        expected = self.credit_repr(
            id=str(credit_db.id),
            createdOn=credit_db.created_dt.date(),
            startDate=credit_db.start_date,
            endDate=credit_db.end_date,
            total=credit_db.effective_amount(),
            allocated=credit_db.get_allocated_amount(),
            available=credit_db.effective_amount() - credit_db.get_allocated_amount(),
            service_fee=service_fee,
            license_fee=license_fee,
            status=credit_db.status,
            currency=credit_db.currency,
        )
        self.assertEqual(expected, credit)

    def test_credits_get(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        credit = magic_mixer.blend(core.features.bcm.CreditLineItem, account=account, end_date=datetime.date.today())

        r = self.client.get(
            reverse("restapi.credit.v1:credits_details", kwargs={"account_id": account.id, "credit_id": credit.id})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_credits_get_credit_doesnt_exist(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])

        r = self.client.get(
            reverse("restapi.credit.v1:credits_details", kwargs={"account_id": account.id, "credit_id": 1234})
        )
        self.assertResponseError(r, "DoesNotExist")

    def test_credits_get_account_doesnt_exist(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        credit = magic_mixer.blend(core.features.bcm.CreditLineItem, agency=agency, end_date=datetime.date.today())

        r = self.client.get(
            reverse("restapi.credit.v1:credits_details", kwargs={"account_id": 12345, "credit_id": credit.id})
        )
        self.assertResponseError(r, "MissingDataError")

    def test_credits_list(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(5).blend(core.features.bcm.CreditLineItem, account=account, end_date=datetime.date.today())

        r = self.client.get(reverse("restapi.credit.v1:credits_list", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_credits_pagination(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(10).blend(dash.models.CreditLineItem, account=account, end_date=datetime.date.today())

        r = self.client.get(reverse("restapi.credit.v1:credits_list", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        marker_id = int(resp_json["data"][5]["id"]) - 1
        r_paginated = self.client.get(
            reverse("restapi.credit.v1:credits_list", kwargs={"account_id": account.id}),
            {"limit": 2, "marker": marker_id},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    def test_service_fee_permissioned(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.BASE_COSTS_SERVICE_FEE])
        credit = magic_mixer.blend(core.features.bcm.CreditLineItem, account=account, end_date=datetime.date.today())

        r = self.client.get(
            reverse("restapi.credit.v1:credits_details", kwargs={"account_id": account.id, "credit_id": credit.id})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"], with_service_fee=True)

    def test_license_fee_permissioned(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.MEDIA_COST_DATA_COST_LICENCE_FEE]
        )
        credit = magic_mixer.blend(core.features.bcm.CreditLineItem, account=account, end_date=datetime.date.today())

        r = self.client.get(
            reverse("restapi.credit.v1:credits_details", kwargs={"account_id": account.id, "credit_id": credit.id})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"], with_license_fee=True)
