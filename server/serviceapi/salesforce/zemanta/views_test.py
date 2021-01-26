import mock
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer
from zemauth.models import User

from . import constants


class CreateClientTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

        magic_mixer.blend(User, email=constants.DEFAULT_CS_REPRESENTATIVE)
        magic_mixer.blend(User, email=constants.DEFAULT_SALES_REPRESENTATIVE)

    def test_put_valid_agency(self):
        data = {"salesforceAccountId": 1, "name": "Agency 1", "type": "agency", "tags": ["some tags", "anOther"]}
        url = reverse("service.salesforce.client")
        r = self.client.put(url, data=data, format="json")
        client = core.models.Agency.objects.all().order_by("-created_dt").first()
        self.assertEqual(r.json(), {"data": {"z1_accountId": client.get_salesforce_id(), "z1_data": "Agency 1"}})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(client.default_account_type, dash.constants.AccountType.PILOT)
        self.assertEqual(client.cs_representative.email, constants.DEFAULT_CS_REPRESENTATIVE)
        self.assertEqual(client.sales_representative.email, constants.DEFAULT_SALES_REPRESENTATIVE)
        self.assertEqual(list(client.entity_tags.all()), ["anOther", "some tags"])

    def test_put_valid_account(self):
        data = {"salesforceAccountId": 1, "name": "Brand 1", "type": "brand", "currency": "EUR", "tags": ["accountTag"]}
        url = reverse("service.salesforce.client")
        r = self.client.put(url, data=data, format="json")
        client = core.models.account.Account.objects.all().order_by("-created_dt").first()
        self.assertEqual(r.json(), {"data": {"z1_accountId": client.get_salesforce_id(), "z1_data": "Brand 1"}})
        self.assertEqual(r.status_code, 200)
        sett = client.get_current_settings()
        self.assertEqual(sett.account_type, dash.constants.AccountType.PILOT)
        self.assertEqual(sett.default_cs_representative.email, constants.DEFAULT_CS_REPRESENTATIVE)
        self.assertEqual(sett.default_sales_representative.email, constants.DEFAULT_SALES_REPRESENTATIVE)
        self.assertEqual(client.currency, dash.constants.Currency.EUR)
        self.assertEqual(list(client.entity_tags.all()), ["accountTag"])

    def test_put_invalid(self):
        url = reverse("service.salesforce.client")

        data = {"salesforceAccountId": 1, "type": "agency"}
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {"details": {"name": ["This field is required."]}, "errorCode": "ValidationError"})

        data = {"salesforceAccountId": 1, "name": "Some name"}
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {"details": {"type": ["This field is required."]}, "errorCode": "ValidationError"})

        data = {"type": "brand", "name": "Some name"}
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(r.status_code, 400)

        self.assertEqual(
            r.json(), {"details": {"salesforceAccountId": ["This field is required."]}, "errorCode": "ValidationError"}
        )

        data = {"salesforceAccountId": 1, "type": "invalid-type", "name": "Some name"}
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"details": {"type": ['"invalid-type" is not a valid choice.']}, "errorCode": "ValidationError"}
        )

        magic_mixer.blend(core.models.Agency, name="Name exists")
        data = {"salesforceAccountId": 1, "type": "agency", "name": "Name exists"}
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"details": {"name": "Name is not unique for this account type."}, "errorCode": "ValidationError"}
        )


class AgencyAccountsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

        self.request_mock = RequestFactory()
        self.request_mock.user = self.user

    def test_valid(self):
        magic_mixer.blend(core.models.Agency, id=1, name="Agency 1").save(self.request_mock)
        magic_mixer.blend(core.models.account.Account, agency_id=None, id=1, name="Acc 0").save(self.request_mock)
        magic_mixer.blend(core.models.account.Account, agency_id=1, id=2, name="Acc 1").save(self.request_mock)
        magic_mixer.blend(core.models.account.Account, agency_id=1, id=3, name="Acc 2").save(self.request_mock)

        url = reverse("service.salesforce.agency_accounts")
        r = self.client.post(url, data={"z1_accountId": "a1"}, format="json")
        self.assertEqual(
            r.json(), {"data": [{"name": "#2 Acc 1", "z1_accountId": "b2"}, {"name": "#3 Acc 2", "z1_accountId": "b3"}]}
        )

    def test_brand(self):
        magic_mixer.blend(core.models.account.Account, agency_id=None, id=1, name="Acc 0").save(self.request_mock)

        url = reverse("service.salesforce.agency_accounts")
        r = self.client.post(url, data={"z1_accountId": "b1"}, format="json")
        self.assertEqual(
            r.json(),
            {"details": {"z1_accountId": ["An agency account must be provided."]}, "errorCode": "ValidationError"},
        )


class CreateCreditTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)

        self.agency = magic_mixer.blend(core.models.Agency, id=1)
        self.account = magic_mixer.blend(core.models.account.Account, id=1, agency=self.agency)

    def test_missing_fields(self):
        url = reverse("service.salesforce.credit")

        data = {}
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(
            r.json(),
            {
                "details": {
                    "amountAtSigning": ["This field is required."],
                    "contractNumber": ["This field is required."],
                    "description": ["This field is required."],
                    "endDate": ["This field is required."],
                    "pfSchedule": ["This field is required."],
                    "salesforceAccountId": ["This field is required."],
                    "salesforceContractId": ["This field is required."],
                    "startDate": ["This field is required."],
                    "z1_accountId": ["This field is required."],
                },
                "errorCode": "ValidationError",
            },
        )

    def test_invalid_fields(self):
        url = reverse("service.salesforce.credit")

        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "endDate": "2017-05-10",
            "startDate": "2017-06-20",
            "pfSchedule": "bla",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "c1",
            "pct_of_budget": "0.1",
        }
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(
            r.json(), {"details": {"pfSchedule": ['"bla" is not a valid choice.']}, "errorCode": "ValidationError"}
        )

    def test_missing_fee(self):
        url = reverse("service.salesforce.credit")

        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "startDate": "2017-05-10",
            "endDate": "2017-06-20",
            "pfSchedule": "monthly as used",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "a1",
        }
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(
            r.json(), {"details": {"nonFieldErrors": ["Fee not provided"]}, "errorCode": "ValidationError"}
        )

    def test_invalid_account(self):
        url = reverse("service.salesforce.credit")
        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "startDate": "2017-05-10",
            "endDate": "2017-06-20",
            "pfSchedule": "monthly as used",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "10",
            "pct_of_budget": "0.1",
        }
        r = self.client.put(url, data=data, format="json")
        self.assertEqual(r.json(), {"details": {"z1_accountId": "Invalid format"}, "errorCode": "ValidationError"})

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_create_agency_credit(self, mock_slack):
        url = reverse("service.salesforce.credit")

        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "startDate": "2017-05-10",
            "endDate": "2017-06-20",
            "pfSchedule": "monthly as used",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "a1",
            "pct_of_budget": "0.1",
            "currency": "EUR",
        }
        r = self.client.put(url, data=data, format="json")
        cli = core.features.bcm.credit_line_item.CreditLineItem.objects.all().order_by("-created_dt").first()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "z1_cliId": cli.pk,
                    "z1_data": {
                        "amount": 500.0,
                        "comment": "Some description",
                        "startDate": "2017-05-10",
                        "licenseFee": 0.1,
                        "endDate": "2017-06-20",
                        "status": 1,
                    },
                }
            },
        )
        mock_slack.assert_called_with(
            None,
            "New agency credit #{credit_id} added to agency <https://one.zemanta.com/v2/credits?agencyId={agency_id}|{agency_name}> with amount €500 and end date 2017-06-20.".format(
                credit_id=cli.pk, agency_id=self.agency.id, agency_name=self.agency.name
            ),
        )
        self.assertEqual(cli.currency, dash.constants.Currency.EUR)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_create_account_credit(self, mock_slack):
        url = reverse("service.salesforce.credit")
        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "startDate": "2017-05-10",
            "endDate": "2017-06-20",
            "pfSchedule": "monthly as used",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "b1",
            "pct_of_budget": "0.1",
        }
        r = self.client.put(url, data=data, format="json")
        cli = core.features.bcm.credit_line_item.CreditLineItem.objects.all().order_by("-created_dt").first()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "z1_cliId": cli.pk,
                    "z1_data": {
                        "amount": 500.0,
                        "comment": "Some description",
                        "startDate": "2017-05-10",
                        "licenseFee": 0.1,
                        "endDate": "2017-06-20",
                        "status": 1,
                    },
                }
            },
        )
        mock_slack.assert_called_with(
            1,
            "New credit #{credit_id} added on account <https://one.zemanta.com/v2/credits?agencyId={agency_id}&accountId={account_id}|{account_name}> with amount $500 and end date 2017-06-20.".format(
                credit_id=cli.pk,
                agency_id=self.account.agency_id,
                account_id=self.account.id,
                account_name=self.account.get_long_name(),
            ),
        )


class CreditsListTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User, email="jonesjoseph@gmail.com")
        self.client.force_authenticate(user=self.user)

        self.request_mock = RequestFactory()
        self.request_mock.user = self.user

    def test_valid_agency(self):
        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency 1")
        agency.save(self.request_mock)
        credit = magic_mixer.blend(
            core.features.bcm.credit_line_item.CreditLineItem,
            amount=100,
            agency=agency,
            created_dt="2018-02-01",
            start_date="2018-02-01",
            end_date="2018-12-31",
            created_by=self.user,
        )

        url = reverse("service.salesforce.credits_list")
        r = self.client.post(url, data={"z1_accountId": "a1"}, format="json")
        self.assertEqual(
            r.json(),
            {
                "data": [
                    {
                        "amount": 100,
                        "comment": "",
                        "contractId": "",
                        "contractNumber": "",
                        "createdBy": "jonesjoseph@gmail.com",
                        "createdDt": credit.created_dt.isoformat(),
                        "currency": "USD",
                        "endDate": "2018-12-31",
                        "licenseFee": "0.2000",
                        "modifiedDt": credit.modified_dt.isoformat(),
                        "refund": False,
                        "specialTerms": "",
                        "startDate": "2018-02-01",
                        "z1_cliId": credit.pk,
                        "status": "PENDING",
                    }
                ]
            },
        )

    def test_valid_account(self):
        account = magic_mixer.blend(core.models.account.Account, id=1, name="Account 1")
        account.save(self.request_mock)
        credit = magic_mixer.blend(
            core.features.bcm.credit_line_item.CreditLineItem,
            amount=100,
            account=account,
            created_dt="2018-02-01",
            start_date="2018-02-01",
            end_date="2018-12-31",
            created_by=self.user,
        )

        url = reverse("service.salesforce.credits_list")
        r = self.client.post(url, data={"z1_accountId": "b1"}, format="json")
        self.assertEqual(
            r.json(),
            {
                "data": [
                    {
                        "amount": 100,
                        "comment": "",
                        "contractId": "",
                        "contractNumber": "",
                        "createdBy": "jonesjoseph@gmail.com",
                        "createdDt": credit.created_dt.isoformat(),
                        "currency": "USD",
                        "endDate": "2018-12-31",
                        "licenseFee": "0.2000",
                        "modifiedDt": credit.modified_dt.isoformat(),
                        "refund": False,
                        "specialTerms": "",
                        "startDate": "2018-02-01",
                        "z1_cliId": credit.pk,
                        "status": "PENDING",
                    }
                ]
            },
        )

    def test_invalid_id(self):
        url = reverse("service.salesforce.credits_list")
        r = self.client.post(url, data={"z1_accountId": "b1234466"}, format="json")
        self.assertEqual(r.json(), {"details": ["No credits found for this ID."], "errorCode": "ValidationError"})
        self.assertEqual(r.status_code, 400)


class AgencyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.user)
        magic_mixer.blend(User, email=constants.DEFAULT_CS_REPRESENTATIVE)
        magic_mixer.blend(User, email=constants.DEFAULT_SALES_REPRESENTATIVE)

        self.cs_representative = magic_mixer.blend(User, email="agency_cs_rep@zemanta.com")
        self.sales_representative = magic_mixer.blend(User, email="agency_sales_rep@zemanta.com")
        self.account1 = magic_mixer.blend(core.models.Account, id=1, name="Account1")
        self.account2 = magic_mixer.blend(core.models.Account, id=2, name="ThisIsTheSecondAccount")
        self.agency = magic_mixer.blend(
            core.models.Agency,
            id=1,
            name="An Agency",
            default_account_type=dash.constants.AccountType.PILOT,
            cs_representative=self.cs_representative,
            sales_representative=self.sales_representative,
        )
        self.agency.entity_tags.add(*["tag1", "tag2"])
        self.agency.account_set.add(self.account1, self.account2)

    def test_get_agency(self):
        url = reverse("service.salesforce.zemanta.agency", kwargs={"agency_id": self.agency.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": 1,
                    "name": "An Agency",
                    "defaultAccountType": 4,
                    "tags": ["tag1", "tag2"],
                    "csRepresentative": "agency_cs_rep@zemanta.com",
                    "salesRepresentative": "agency_sales_rep@zemanta.com",
                    "z1_accountId": "a1",
                    "accounts": [
                        {"name": "Account1", "z1_accountId": "b1"},
                        {"name": "ThisIsTheSecondAccount", "z1_accountId": "b2"},
                    ],
                }
            },
        )

    def test_get_agency_valid_sfid(self):
        url = reverse("service.salesforce.zemanta.agency") + "a{}".format(self.agency.id)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.json(),
            {
                "data": {
                    "id": 1,
                    "name": "An Agency",
                    "defaultAccountType": 4,
                    "tags": ["tag1", "tag2"],
                    "csRepresentative": "agency_cs_rep@zemanta.com",
                    "salesRepresentative": "agency_sales_rep@zemanta.com",
                    "z1_accountId": "a1",
                    "accounts": [
                        {"name": "Account1", "z1_accountId": "b1"},
                        {"name": "ThisIsTheSecondAccount", "z1_accountId": "b2"},
                    ],
                }
            },
        )

    def test_get_agency_invalid_sfid(self):
        url = reverse("service.salesforce.zemanta.agency") + "b{}".format(self.agency.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_get_agency_missing(self):
        url = reverse("service.salesforce.zemanta.agency", kwargs={"agency_id": 1234})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(), {"errorCode": "ValidationError", "details": {"entity": "Agency does not exists"}}
        )

    def test_create_agency_defaults(self):
        url = reverse("service.salesforce.zemanta.agency")
        payload = {"name": "new Agency", "clientType": "Agency", "clientSize": "Big6", "region": "NA-US"}
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 200)
        new_agency = core.models.Agency.objects.get(name="new Agency")
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": new_agency.id,
                    "name": "new Agency",
                    "tags": ["dmr/Agency", "dmr/Big6", "dmr/NA/US"],
                    "csRepresentative": constants.DEFAULT_CS_REPRESENTATIVE,
                    "salesRepresentative": constants.DEFAULT_SALES_REPRESENTATIVE,
                    "defaultAccountType": constants.DEFAULT_ACCOUNT_TYPE,
                    "z1_accountId": f"a{new_agency.id}",
                    "accounts": [],
                }
            },
        )

    def test_create_agency_tags(self):
        url = reverse("service.salesforce.zemanta.agency")

        payload = {"name": "new Agency 1", "clientType": "Agency", "clientSize": "Indie", "region": "NA-US"}
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(set(response.json()["data"]["tags"]), {"dmr/Agency", "dmr/Indie", "dmr/NA/US"})

        payload = {"name": "new Agency 2", "clientType": "Publisher", "region": "NA-US"}
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(set(response.json()["data"]["tags"]), {"dmr/Publisher", "dmr/NA/US"})

        payload = {"name": "new Agency 3", "clientType": "PaaS", "region": "EU-IT"}
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(set(response.json()["data"]["tags"]), {"dmr/PaaS", "dmr/EU/IT"})

        payload = {"name": "new Agency 4", "clientType": "PaaS", "region": "APAC"}
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(set(response.json()["data"]["tags"]), {"dmr/PaaS", "dmr/APAC"})

    def test_create_agency_custom_attributes(self):
        url = reverse("service.salesforce.zemanta.agency")
        payload = {
            "name": "new Agency 1",
            "clientType": "Agency",
            "clientSize": "Indie",
            "region": "NA-US",
            "customAttributes": ["Publisher", "SocialAgg"],
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            set(response.json()["data"]["tags"]),
            {"dmr/Agency", "dmr/Indie", "dmr/NA/US", "dmr/custom/Publisher", "dmr/custom/SocialAgg"},
        )

    def test_create_agency_custom_attributes_invalid(self):
        url = reverse("service.salesforce.zemanta.agency")
        payload = {
            "name": "new Agency 1",
            "clientType": "Agency",
            "clientSize": "Indie",
            "region": "NA-US",
            "customAttributes": ["Publisher", "Social Agg"],
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEquals(response.status_code, 400)

    def test_create_agency_invalid(self):
        url = reverse("service.salesforce.zemanta.agency")

        data = {"name": self.agency.name}
        r = self.client.post(url, data=data, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(),
            {
                "errorCode": "ValidationError",
                "details": ["{'name': [ErrorDetail(string='agency with this name already exists.', code='unique')]}"],
            },
        )
