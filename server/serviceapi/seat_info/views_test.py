from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

import core.models
from utils.magic_mixer import magic_mixer
from zemauth.models import User


class SeatInfoTestCase(TestCase):
    def setUp(self):
        self.service_user = magic_mixer.blend(User, email="seatinfo@service.zemanta.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.service_user)
        self.ob_sales_repr = magic_mixer.blend(User, outbrain_user_id="1234", id=1)
        self.ob_account_mgr = magic_mixer.blend(User, outbrain_user_id="456", id=2)
        self.account_mgr = magic_mixer.blend(User, outbrain_user_id="789", id=3)
        self.sales_repr = magic_mixer.blend(User, outbrain_user_id="12", id=4)

    def test_get_seatinfo_account(self):
        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency test")
        agency.entity_tags.add("outbrain/sales/OutbrainSalesforce")
        account = magic_mixer.blend(core.models.Account, agency=agency, id=1, name="Account test")
        account.settings.update(
            None,
            ob_sales_representative=self.ob_sales_repr,
            ob_account_manager=self.ob_account_mgr,
            default_account_manager=self.account_mgr,
            default_sales_representative=self.sales_repr,
        )

        url = reverse("service.seatinfo.seats", kwargs={"seat_id": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "agencyName": "Agency test",
                    "agencyId": 1,
                    "accountName": "Account test",
                    "accountId": 1,
                    "obSalesRepresentativeId": "12",
                    "obAccountManagerId": "789",
                    "isZmsAccount": True,
                }
            },
        )

    def test_get_self_managed_account(self):
        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency test")
        account = magic_mixer.blend(core.models.Account, agency=agency, id=1, name="Account test")
        account.settings.update(
            None,
            ob_sales_representative=self.ob_sales_repr,
            ob_account_manager=self.ob_account_mgr,
            default_account_manager=self.account_mgr,
            default_sales_representative=self.sales_repr,
        )

        url = reverse("service.seatinfo.seats", kwargs={"seat_id": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "agencyName": "Agency test",
                    "agencyId": 1,
                    "accountName": "Account test",
                    "accountId": 1,
                    "obSalesRepresentativeId": "1234",
                    "obAccountManagerId": "456",
                    "isZmsAccount": False,
                }
            },
        )

    def test_get_account_does_not_exist(self):
        url = reverse("service.seatinfo.seats", kwargs={"seat_id": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"errorCode": "MissingDataError", "details": "Account does not exist"})

    def test_get_account_without_representatives(self):
        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency test")
        account = magic_mixer.blend(core.models.Account, agency=agency, id=1, name="Account test")
        account.settings.update(
            None,
            ob_sales_representative=None,
            ob_account_manager=None,
            default_account_manager=None,
            default_sales_representative=None,
        )

        url = reverse("service.seatinfo.seats", kwargs={"seat_id": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "agencyName": "Agency test",
                    "agencyId": 1,
                    "accountName": "Account test",
                    "accountId": 1,
                    "obSalesRepresentativeId": None,
                    "obAccountManagerId": None,
                    "isZmsAccount": False,
                }
            },
        )

    def test_get_account_without_agency(self):
        account = magic_mixer.blend(core.models.Account, id=1, name="Account test")
        account.settings.update(
            None,
            ob_sales_representative=self.ob_sales_repr,
            ob_account_manager=self.ob_account_mgr,
            default_account_manager=self.account_mgr,
            default_sales_representative=self.sales_repr,
        )

        url = reverse("service.seatinfo.seats", kwargs={"seat_id": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "agencyName": None,
                    "agencyId": None,
                    "accountName": "Account test",
                    "accountId": 1,
                    "obSalesRepresentativeId": "1234",
                    "obAccountManagerId": "456",
                    "isZmsAccount": False,
                }
            },
        )
