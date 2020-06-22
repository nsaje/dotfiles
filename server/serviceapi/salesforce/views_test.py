import datetime

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
        self.assertEqual(list(client.entity_tags.all()), ["some tags", "anOther"])

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
                        "amount": 500,
                        "comment": "Some description",
                        "startDate": "2017-05-10",
                        "flatFeeCc": 0,
                        "flatFeeEndDate": None,
                        "flatFeeStartDate": None,
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
                        "amount": 500,
                        "comment": "Some description",
                        "startDate": "2017-05-10",
                        "flatFeeCc": 0,
                        "flatFeeEndDate": None,
                        "flatFeeStartDate": None,
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

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_flat_fee_upfront(self, mock_slack):
        url = reverse("service.salesforce.credit")
        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "endDate": "2017-06-20",
            "startDate": "2017-05-10",
            "pfSchedule": "upon execution of this agreement",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "b1",
            "calc_variable_fee": "100.0",
        }
        r = self.client.put(url, data=data, format="json")
        cli = core.features.bcm.credit_line_item.CreditLineItem.objects.all().order_by("-created_dt").first()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "z1_cliId": cli.pk,
                    "z1_data": {
                        "amount": 500,
                        "comment": "Some description",
                        "endDate": "2017-06-20",
                        "flatFeeCc": 1000000,
                        "flatFeeEndDate": "2017-05-10",
                        "flatFeeStartDate": "2017-05-10",
                        "licenseFee": 0.0,
                        "startDate": "2017-05-10",
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

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_flat_fee(self, mock_slack):
        url = reverse("service.salesforce.credit")
        data = {
            "amountAtSigning": "500.0",
            "billingContract": "contract",
            "contractNumber": "00",
            "description": "Some description",
            "startDate": "2017-05-10",
            "endDate": "2017-06-20",
            "pfSchedule": "monthly in installments",
            "salesforceAccountId": "123",
            "salesforceContractId": "111",
            "z1_accountId": "b1",
            "calc_variable_fee": "100.0",
        }
        r = self.client.put(url, data=data, format="json")
        cli = core.features.bcm.credit_line_item.CreditLineItem.objects.all().order_by("-created_dt").first()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "z1_cliId": cli.pk,
                    "z1_data": {
                        "amount": 500,
                        "comment": "Some description",
                        "startDate": "2017-05-10",
                        "flatFeeCc": 1000000,
                        "flatFeeEndDate": "2017-06-20",
                        "flatFeeStartDate": "2017-05-10",
                        "licenseFee": 0.0,
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
                        "flatFeeCc": 0,
                        "flatFeeEndDate": None,
                        "flatFeeStartDate": None,
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
                        "flatFeeCc": 0,
                        "flatFeeEndDate": None,
                        "flatFeeStartDate": None,
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


@mock.patch("django.utils.timezone.now", return_value=datetime.datetime(2019, 3, 2))
class AgencyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.service_user = magic_mixer.blend(User, email="outbrain-salesforce@service.zemanta.com")
        self.user = magic_mixer.blend(User)
        self.client.force_authenticate(user=self.service_user)
        self.request_mock = RequestFactory()
        self.request_mock.user = self.user

    def test_get(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=1, name="Agency 1", is_externally_managed=True)
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 1})
        response = self.client.get(url)
        self.assertEqual(
            response.data,
            {
                "data": {
                    "id": 1,
                    "is_disabled": False,
                    "name": "Agency 1",
                    "tags": [],
                    "modified_dt": "02-03-2019",
                    "custom_attributes": {},
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )

    def test_get_agency_does_not_exist(self, mock_modified_dt):
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 1234})
        response = self.client.get(url)
        self.assertEqual(
            response.data, {"errorCode": "DoesNotExist", "details": "Agency matching query does not exist."}
        )

    def test_get_agency_not_externally_managed(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=1, name="Agency 1", is_externally_managed=False)
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 1})
        response = self.client.get(url)
        self.assertEqual(
            response.data, {"errorCode": "DoesNotExist", "details": "Agency matching query does not exist."}
        )

    def test_post_valid(self, mock_modified_dt):
        url = reverse("service.salesforce.agency")
        r = self.client.post(
            url,
            data={
                "name": "new Agency",
                "tags": ["first tags", "second new tag"],
                "custom_attributes": {"country": "SI"},
            },
            format="json",
        )
        # self.assertEqual(r.status_code, 200)
        new_agency = core.models.Agency.objects.filter(name="new Agency").first()
        self.assertIsNotNone(new_agency)

        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": new_agency.id,
                    "name": "new Agency",
                    "is_disabled": False,
                    "tags": ["first tags", "second new tag"],
                    "custom_attributes": {"country": "SI"},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )

    def test_post_valid_custom_attributes(self, mock_modified_dt):
        url = reverse("service.salesforce.agency")
        r = self.client.post(url, data={"name": "new Agency", "custom_attributes": ["country"]}, format="json")
        new_agency = core.models.Agency.objects.filter(name="new Agency").first()
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(new_agency)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "customAttributes": ["country"],
                    "id": new_agency.id,
                    "isDisabled": False,
                    "name": "new Agency",
                    "tags": [],
                    "modifiedDt": "02-03-2019",
                    "isExternallyManaged": True,
                    "amplifyReview": True,
                }
            },
        )

    def test_post_valid_disabled(self, mock_modified_dt):
        url = reverse("service.salesforce.agency")
        r = self.client.post(
            url,
            data={"name": "new Agency", "is_disabled": True, "tags": ["first tags", "second new tag"]},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        new_agency = core.models.Agency.objects.filter(name="new Agency").first()
        self.assertIsNotNone(new_agency)

        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": new_agency.id,
                    "name": "new Agency",
                    "is_disabled": True,
                    "tags": ["first tags", "second new tag"],
                    "custom_attributes": {},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )

    def test_post_invalid_name(self, mock_modified_dt):
        url = reverse("service.salesforce.agency")
        r = self.client.post(url, data={"name": "", "tags": ["first tags", "second new tag"]}, format="json")
        self.assertEqual(r.status_code, 400)
        new_agency = core.models.Agency.objects.filter(name="new Agency").first()
        self.assertIsNone(new_agency)

        self.assertEqual(
            r.data, {"details": {"name": ["This field may not be blank."]}, "errorCode": "ValidationError"}
        )

        core.models.Agency.objects.create(self.request_mock, name="new Agency")
        self.assertTrue(core.models.Agency.objects.filter(name="new Agency").exists(), True)
        r = self.client.post(url, data={"name": "new Agency", "tags": ["first tags", "second new tag"]}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"details": {"name": ["agency with this name already exists."]}, "errorCode": "ValidationError"}
        )

    def test_put_valid(self, mock_modified_dt):
        # Set New Name, new tags
        magic_mixer.blend(core.models.Agency, id=2, name="Agency 1", is_externally_managed=True)
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 2})
        r = self.client.put(url, data={"name": "New Name", "tags": ["New tags"]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": 2,
                    "name": "New Name",
                    "is_disabled": False,
                    "tags": ["New tags"],
                    "custom_attributes": {},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )

    def test_put_valid_tags(self, mock_modified_dt):
        agency = magic_mixer.blend(core.models.Agency, id=2, name="Agency 1", is_externally_managed=True)
        agency.entity_tags.add(*["New tags"])
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 2})

        # Set tags
        r = self.client.put(url, data={"tags": ["An Other"]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": 2,
                    "name": "Agency 1",
                    "is_disabled": False,
                    "tags": ["An Other"],
                    "custom_attributes": {},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )

        # Clear tags
        self.assertEqual(core.models.Agency.objects.get(id=2).entity_tags, ["An Other"])
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 2})
        r = self.client.put(url, data={"tags": []}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": 2,
                    "name": "Agency 1",
                    "is_disabled": False,
                    "tags": [],
                    "custom_attributes": {},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )

    def test_put_valid_custom_attributes(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=2, name="Agency 1", is_externally_managed=True)
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 2})

        # Set custom attributes
        r = self.client.put(url, data={"custom_attributes": {"country": "SI"}}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["data"]["custom_attributes"], {"country": "SI"})

        # Unset custom attributes
        r = self.client.put(url, data={"custom_attributes": {}}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["data"]["custom_attributes"], {})

        # Set custom attributes as array
        r = self.client.put(url, data={"custom_attributes": ["country"]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["data"]["custom_attributes"], ["country"])

        # UnSet custom attributes as array
        r = self.client.put(url, data={"custom_attributes": []}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["data"]["custom_attributes"], [])

    def test_put_disable(self, mock_modified_dt):
        agency = magic_mixer.blend(core.models.Agency, id=3, name="Agency 1", is_externally_managed=True)
        magic_mixer.blend(
            core.models.Account,
            agency=agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=False,
        )
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 3})
        r = self.client.put(
            url,
            data={"name": "New Name", "is_disabled": True, "tags": [], "custom_attributes": {"country": "SI"}},
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": 3,
                    "name": "New Name",
                    "is_disabled": True,
                    "tags": [],
                    "custom_attributes": {"country": "SI"},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )
        self.assertEqual(core.models.Account.objects.get(id=1).is_disabled, True)

        r = self.client.put(url, data={"is_disabled": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": 3,
                    "name": "New Name",
                    "is_disabled": False,
                    "tags": [],
                    "custom_attributes": {"country": "SI"},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )
        self.assertEqual(core.models.Account.objects.get(id=1).is_disabled, False)

    def test_put_invalid_change_is_externally_managed(self, mock_modified_dt):
        # Set New Name, new tags
        ag = magic_mixer.blend(core.models.Agency, id=2, name="Agency 1", is_externally_managed=True)
        url = reverse("service.salesforce.agency", kwargs={"agency_id": 2})
        r = self.client.put(url, data={"is_externally_managed": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": 2,
                    "name": "Agency 1",
                    "is_disabled": False,
                    "tags": [],
                    "custom_attributes": {},
                    "modified_dt": "02-03-2019",
                    "is_externally_managed": True,
                    "amplify_review": True,
                }
            },
        )
        self.assertEqual(ag.is_externally_managed, True)

    def test_list_valid_created_dt_filter(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=2, name="ag2", is_externally_managed=True)

        url = reverse("service.salesforce.agencies")
        r = self.client.get(url, data={"created_dt_start": "01-03-2019", "created_dt_end": "31-03-2019"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            [
                {
                    "id": 2,
                    "name": "ag2",
                    "tags": [],
                    "modifiedDt": "02-03-2019",
                    "isDisabled": False,
                    "customAttributes": {},
                    "isExternallyManaged": True,
                    "amplifyReview": True,
                }
            ],
        )

    def test_list_filter_invalid_parameters(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=2, name="ag2", is_externally_managed=True)

        url = reverse("service.salesforce.agencies")
        r = self.client.get(url, data={"start_date": "2019-03-01", "end_date": "2019-03-01"})
        # self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"details": ["Query parameters must be provided."], "errorCode": "ListNoParametersProvided"}
        )


@mock.patch("django.utils.timezone.now", return_value=datetime.datetime(2019, 3, 2))
class AccountTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.service_user = magic_mixer.blend(User, email="outbrain-salesforce@service.zemanta.com")
        self.user = magic_mixer.blend(User, email="salesRep@test.com")
        self.user2 = magic_mixer.blend(User, email="accountManager@test.com")
        self.aguser = magic_mixer.blend(User, email="agencysalesrep@test.com")
        self.aguser2 = magic_mixer.blend(User, email="agencyaccountmgr@test.com")
        self.outbrainAgencyUser = magic_mixer.blend(User, email="OutbrainAgencyUser@test.com")
        self.notInMappingUser = magic_mixer.blend(User, email="notInMapping@test.com")
        self.client.force_authenticate(user=self.service_user)
        self.request_mock = RequestFactory()
        self.request_mock.user = self.user
        self.agency = magic_mixer.blend(
            core.models.Agency, id=3, name="Agency 1", is_externally_managed=True, sales_representative=self.aguser
        )
        self.video_agency = magic_mixer.blend(
            core.models.Agency, id=221, name="video Agency", is_externally_managed=True
        )
        self.Outbrain_unknown_Agency = magic_mixer.blend(
            core.models.Agency, id=517, name="Outbrain ZMS Unknown", is_externally_managed=True
        )
        constants.SALES_REP_AGENCY_MAPPING = {"OutbrainAgencyUser@test.com": 3}

    def test_get(self, mock_modified_dt):
        magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
        )

        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.get(url)
        self.assertEqual(
            response.data,
            {
                "data": {
                    "id": 1,
                    "agency_id": 3,
                    "is_disabled": True,
                    "name": "Account 1",
                    "salesforce_url": "http://salesforce.com",
                    "currency": "USD",
                    "sales_representative": None,
                    "account_manager": None,
                    "tags": [],
                    "custom_attributes": {},
                    "salesforce_id": 123,
                    "modified_dt": "02-03-2019",
                    "is_archived": False,
                    "is_externally_managed": True,
                    "internal_marketer_id": None,
                    "external_marketer_id": None,
                    "amplify_review": True,
                }
            },
        )

    def test_get_account_does_not_exist(self, mock_modified_dt):
        url = reverse("service.salesforce.account", kwargs={"account_id": 1234})
        response = self.client.get(url)
        self.assertEqual(
            response.data, {"errorCode": "DoesNotExist", "details": "Account matching query does not exist."}
        )

    def test_get_account_not_externally_managed(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=3, name="Agency 3", is_externally_managed=False)
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.get(url)
        self.assertEqual(
            response.data, {"errorCode": "DoesNotExist", "details": "Account matching query does not exist."}
        )

    def test_post_valid_with_id(self, mock_modified_dt):
        core.models.OutbrainAccount.objects.create(marketer_id="EXTERNAL ID", used=False)

        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 3,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "salesRep@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI"},
                "salesforce_id": 123,
                "internal_marketer_id": "INTERNAL ID",
                "external_marketer_id": "EXTERNAL ID",
            },
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNotNone(new_account)
        self.assertTrue(core.models.OutbrainAccount.objects.filter(marketer_id="EXTERNAL ID", used=True).exists())
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": new_account.id,
                    "agency_id": 3,
                    "is_disabled": True,
                    "name": "new Account",
                    "salesforce_url": "http://salesforce.com",
                    "currency": "CHF",
                    "sales_representative": "salesRep@test.com",
                    "account_manager": "accountManager@test.com",
                    "tags": ["tag1", "tag2"],
                    "custom_attributes": {"country": "SI"},
                    "salesforce_id": 123,
                    "modified_dt": "02-03-2019",
                    "is_archived": False,
                    "is_externally_managed": True,
                    "internal_marketer_id": "INTERNAL ID",
                    "external_marketer_id": "EXTERNAL ID",
                    "amplify_review": True,
                }
            },
        )

    def test_post_valid_with_sales_rep(self, mock_modified_dt):
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "OutbrainAgencyUser@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI"},
                "salesforce_id": 123,
                "internal_marketer_id": "INTERNAL ID",
                "external_marketer_id": "EXTERNAL ID",
            },
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNotNone(new_account)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": new_account.id,
                    "agency_id": 3,
                    "is_disabled": True,
                    "name": "new Account",
                    "salesforce_url": "http://salesforce.com",
                    "currency": "CHF",
                    "sales_representative": "OutbrainAgencyUser@test.com",
                    "account_manager": "accountManager@test.com",
                    "tags": ["tag1", "tag2"],
                    "custom_attributes": {"country": "SI"},
                    "salesforce_id": 123,
                    "modified_dt": "02-03-2019",
                    "is_archived": False,
                    "is_externally_managed": True,
                    "internal_marketer_id": "INTERNAL ID",
                    "external_marketer_id": "EXTERNAL ID",
                    "amplify_review": True,
                }
            },
        )

    def test_post_valid_with_advertiserAccountType(self, mock_modified_dt):
        self.maxDiff = None
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 3,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "salesRep@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI", "advertiserAccountType": constants.VIDEO_ADVERTISER_TYPE},
                "salesforce_id": 123,
                "internal_marketer_id": "INTERNAL ID",
                "external_marketer_id": "EXTERNAL ID",
            },
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNotNone(new_account)

        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": new_account.id,
                    "agency_id": 221,
                    "is_disabled": True,
                    "name": "new Account",
                    "salesforce_url": "http://salesforce.com",
                    "currency": "CHF",
                    "sales_representative": "salesRep@test.com",
                    "account_manager": "accountManager@test.com",
                    "tags": ["tag1", "tag2"],
                    "custom_attributes": {"country": "SI", "advertiser_account_type": constants.VIDEO_ADVERTISER_TYPE},
                    "salesforce_id": 123,
                    "modified_dt": "02-03-2019",
                    "is_archived": False,
                    "is_externally_managed": True,
                    "internal_marketer_id": "INTERNAL ID",
                    "external_marketer_id": "EXTERNAL ID",
                    "amplify_review": True,
                }
            },
        )

    def test_post_with_sales_rep_not_in_mapping(self, mock_modified_dt):
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "notInMapping@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI"},
                "salesforce_id": 123,
                "internal_marketer_id": "INTERNAL ID",
                "external_marketer_id": "EXTERNAL ID",
            },
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNotNone(new_account)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": new_account.id,
                    "name": "new Account",
                    "salesforceUrl": "http://salesforce.com",
                    "salesforceId": 123,
                    "isDisabled": True,
                    "customAttributes": {"country": "SI"},
                    "currency": "CHF",
                    "agencyId": 517,
                    "salesRepresentative": "notInMapping@test.com",
                    "accountManager": "accountManager@test.com",
                    "tags": ["tag1", "tag2"],
                    "isArchived": False,
                    "modifiedDt": "02-03-2019",
                    "isExternallyManaged": True,
                    "externalMarketerId": "EXTERNAL ID",
                    "internalMarketerId": "INTERNAL ID",
                    "amplifyReview": True,
                }
            },
        )

    def test_post_valid_no_sales_representative(self, mock_modified_dt):
        # If no sales rep set on account, the one from the agency must be set as default
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 3,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI"},
                "salesforce_id": 123,
                "amplify_review": True,
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNone(new_account)
        self.assertEqual(
            r.json(), {"errorCode": "ValidationError", "details": {"salesRepresentative": ["This field is required."]}}
        )

    def test_post_valid_no_account_manager(self, mock_modified_dt):
        # If no account manager set on account, the one from the agency must be set as default
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 3,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "agencysalesrep@test.com",
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI"},
                "salesforce_id": 123,
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNotNone(new_account)
        self.assertEqual(
            r.data,
            {
                "data": {
                    "id": new_account.id,
                    "agency_id": 3,
                    "is_disabled": True,
                    "name": "new Account",
                    "salesforce_url": "http://salesforce.com",
                    "currency": "CHF",
                    "sales_representative": "agencysalesrep@test.com",
                    "account_manager": "outbrain-salesforce@service.zemanta.com",
                    "tags": ["tag1", "tag2"],
                    "custom_attributes": {"country": "SI"},
                    "salesforce_id": 123,
                    "modified_dt": "02-03-2019",
                    "is_archived": False,
                    "is_externally_managed": True,
                    "internal_marketer_id": None,
                    "external_marketer_id": None,
                    "amplify_review": True,
                }
            },
        )

    def test_post_invalid_agency_not_exists(self, mock_modified_dt):
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 123,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "salesRep@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNone(new_account)
        self.assertEqual(
            r.json(),
            {"details": {"agencyId": ['Invalid pk "123" - object does not exist.']}, "errorCode": "ValidationError"},
        )

    def test_post_invalid_agency_not_externally_managed(self, mock_modified_dt):
        magic_mixer.blend(core.models.Agency, id=4, name="Agency 4", is_externally_managed=False)
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 4,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "salesRep@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNone(new_account)
        self.assertEqual(
            r.json(),
            {
                "details": {"agencyId": ["Agency provided does not exists or is not externally manageable."]},
                "errorCode": "ValidationError",
            },
        )

    def test_post_invalid_sales_rep(self, mock_modified_dt):
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 3,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "someone@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNone(new_account)
        self.assertEqual(
            r.json(),
            {
                "details": {"salesRepresentative": ["Sales representative e-mail not found."]},
                "errorCode": "ValidationError",
            },
        )

    def test_post_invalid_account_manager(self, mock_modified_dt):
        url = reverse("service.salesforce.account")
        r = self.client.post(
            url,
            data={
                "agency_id": 3,
                "is_disabled": True,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "currency": "CHF",
                "sales_representative": "salesRep@test.com",
                "account_manager": "someoneelse@test.com",
                "tags": ["tag1", "tag2"],
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        new_account = core.models.Account.objects.filter(name="new Account").first()
        self.assertIsNone(new_account)
        self.assertEqual(
            r.json(),
            {"details": {"accountManager": ["Account manager e-mail not found."]}, "errorCode": "ValidationError"},
        )

    def test_post_invalid_account_agency_disabled(self, mock_modified_dt):
        agency = magic_mixer.blend(
            core.models.Agency, id=4, name="new Agency", is_externally_managed=True, is_disabled=True
        )
        magic_mixer.blend(core.models.Account, id=3, name="Account 1", agency=agency)
        url = reverse("service.salesforce.account")
        response = self.client.post(
            url,
            data={
                "agency_id": 4,
                "is_disabled": False,
                "name": "new Account",
                "salesforce_url": "http://salesforce.com",
                "sales_representative": "salesRep@test.com",
                "account_manager": "accountManager@test.com",
                "tags": ["tag1", "tag2"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "details": {"agencyId": ["Creating account on a disabled agency is not allowed."]},
                "errorCode": "ValidationError",
            },
        )

    def test_put_valid(self, mock_modified_dt):
        acc = magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
            outbrain_marketer_id="marketer 1234",
            outbrain_internal_marketer_id="marketer 0987",
        )
        acc.save(None)
        acc.settings.update(None, default_account_manager=self.user2, default_sales_representative=self.user)
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.put(
            url,
            data={
                "name": "Account 1",
                "is_disabled": False,
                "tags": ["tag1", "tag2"],
                "custom_attributes": {"country": "SI"},
                "salesforce_id": 456,
                "sales_representative": "agencysalesrep@test.com",
                "account_manager": "agencyaccountmgr@test.com",
                "external_marketer_id": "new external marketer",
                "internal_marketer_id": "new internal marketer",
                "amplify_review": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "data": {
                    "id": 1,
                    "agency_id": 3,
                    "is_disabled": False,
                    "name": "Account 1",
                    "salesforce_url": "http://salesforce.com",
                    "currency": "USD",
                    "sales_representative": "agencysalesrep@test.com",
                    "account_manager": "agencyaccountmgr@test.com",
                    "tags": ["tag1", "tag2"],
                    "custom_attributes": {"country": "SI"},
                    "salesforce_id": 456,
                    "modified_dt": "02-03-2019",
                    "is_archived": False,
                    "is_externally_managed": True,
                    "external_marketer_id": "new external marketer",
                    "internal_marketer_id": "new internal marketer",
                    "amplify_review": True,
                }
            },
        )

    def test_put_marketer(self, mock_modified_dt):
        # create a new OB account
        acc = magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
        )
        acc.save(None)
        acc.settings.update(None, default_account_manager=self.user2, default_sales_representative=self.user)
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.put(
            url, data={"external_marketer_id": "1234", "internal_marketer_id": "09876"}, format="json"
        )
        self.assertEqual(response.data["data"]["external_marketer_id"], "1234")
        self.assertEqual(response.data["data"]["internal_marketer_id"], "09876")
        self.assertTrue(core.models.OutbrainAccount.objects.filter(marketer_id="1234", used=True).exists())

        # with existing OB account
        new_ob_account = core.models.OutbrainAccount.objects.create(marketer_id="qwerty", used=False)
        acc2 = magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=2,
            name="Account 2",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
        )
        acc2.save(None)
        acc2.settings.update(None, default_account_manager=self.user2, default_sales_representative=self.user)
        url = reverse("service.salesforce.account", kwargs={"account_id": 2})
        response = self.client.put(
            url, data={"external_marketer_id": "qwerty", "internal_marketer_id": "09876"}, format="json"
        )
        self.assertEqual(response.data["data"]["external_marketer_id"], "qwerty")
        self.assertEqual(response.data["data"]["internal_marketer_id"], "09876")
        new_ob_account.refresh_from_db()
        self.assertTrue(new_ob_account.used)

    def test_put_valid_set_tags(self, mock_modified_dt):
        account = magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=False,
            salesforce_id=123,
        )
        account.entity_tags.add(*["New tags"])
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})

        r = self.client.put(url, data={"tags": ["An Other"]}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["data"]["tags"], ["An Other"])

    def test_put_valid_unset_tags(self, mock_modified_dt):
        magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
        )
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.put(url, data={"tags": []}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["tags"], [])

    def test_put_valid_custom_attributes(self, mock_modified_dt):
        # Set custom attributes
        magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
        )
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.put(url, data={"custom_attributes": {"country": "SI"}}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["custom_attributes"], {"country": "SI"})

    def test_put_marketer_ids(self, mock_modified_dt):
        # Set custom attributes
        magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
            outbrain_mareketer_id="1234",
            outbrain_external_marketer_id="0987",
        )
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.put(
            url, data={"internal_marketer_id": "NEW INTERNAL", "external_marketer_id": "NEW EXTERNAL"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        self.assertEqual(response.data["data"]["internal_marketer_id"], "NEW INTERNAL")
        self.assertEqual(response.data["data"]["external_marketer_id"], "NEW EXTERNAL")

    def test_put_valid_unset_custom_attributes(self, mock_modified_dt):
        # Unset custom attributes
        magic_mixer.blend(
            core.models.Account,
            agency=self.agency,
            id=1,
            name="Account 1",
            salesforce_url="http://salesforce.com",
            is_disabled=True,
            salesforce_id=123,
            custom_attributes={"country": "SI"},
        )
        url = reverse("service.salesforce.account", kwargs={"account_id": 1})
        response = self.client.put(url, data={"custom_attributes": {}}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["custom_attributes"], {})

    def test_put_valid_disable(self, mock_modified_dt):
        magic_mixer.blend(core.models.Account, id=3, name="Account 1", agency=self.agency, salesforce_id=123)
        url = reverse("service.salesforce.account", kwargs={"account_id": 3})
        response = self.client.put(url, data={"is_disabled": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["is_disabled"], True)

    def test_put_invalid_account_not_exists(self, mock_modified_dt):
        magic_mixer.blend(core.models.Account, id=3, name="No agency Account")
        url = reverse("service.salesforce.account", kwargs={"account_id": 3})
        response = self.client.put(url, data={"name": "new Name"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {"errorCode": "DoesNotExist", "details": "Account matching query does not exist."}
        )

    def test_put_invalid_change_currency(self, mock_modified_dt):
        magic_mixer.blend(core.models.Account, id=3, name="Account 1", agency=self.agency)
        url = reverse("service.salesforce.account", kwargs={"account_id": 3})
        response = self.client.put(url, data={"currency": "EUR"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": 3,
                    "name": "Account 1",
                    "salesforceUrl": None,
                    "salesforceId": None,
                    "currency": "USD",
                    "isDisabled": False,
                    "customAttributes": {},
                    "agencyId": 3,
                    "salesRepresentative": None,
                    "accountManager": None,
                    "tags": [],
                    "isArchived": False,
                    "modifiedDt": "02-03-2019",
                    "isExternallyManaged": True,
                    "externalMarketerId": None,
                    "internalMarketerId": None,
                    "amplifyReview": True,
                }
            },
        )

    def test_list_invalid_no_params(self, mock_modified_dt):
        magic_mixer.blend(
            core.models.Account,
            id=1,
            name="ac1",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac2",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        magic_mixer.blend(
            core.models.Account,
            id=3,
            name="ac3",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        magic_mixer.blend(
            core.models.Account,
            id=4,
            name="ac4",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )

        url = reverse("service.salesforce.accounts")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"errorCode": "ListNoParametersProvided", "details": ["Query parameters must be provided."]}
        )

    def test_list_filter_valid_created_dt(self, mock_modified_dt):
        magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac2",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )

        url = reverse("service.salesforce.accounts")
        r = self.client.get(url, data={"created_dt_start": "02-03-2019", "created_dt_end": "30-03-2019"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            [
                {
                    "id": 2,
                    "name": "ac2",
                    "agencyId": 3,
                    "salesforceUrl": None,
                    "salesforceId": 123,
                    "currency": "USD",
                    "salesRepresentative": None,
                    "accountManager": None,
                    "isDisabled": False,
                    "tags": [],
                    "customAttributes": {},
                    "modifiedDt": "02-03-2019",
                    "isArchived": False,
                    "isExternallyManaged": True,
                    "externalMarketerId": None,
                    "internalMarketerId": None,
                    "amplifyReview": True,
                }
            ],
        )

    def test_list_filter_valid_modified_dt(self, mock_modified_dt):
        ac1 = magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac1",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac2",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        mock_modified_dt.return_value = datetime.datetime(2019, 3, 4)
        ac1.update(None, name="new name")

        url = reverse("service.salesforce.accounts")
        r = self.client.get(url, data={"modified_dt_start": "04-03-2019", "modified_dt_end": "30-03-2019"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            [
                {
                    "id": 2,
                    "name": "new name",
                    "agencyId": 3,
                    "salesforceUrl": None,
                    "salesforceId": 123,
                    "currency": "USD",
                    "salesRepresentative": None,
                    "accountManager": None,
                    "isDisabled": False,
                    "tags": [],
                    "customAttributes": {},
                    "modifiedDt": "04-03-2019",
                    "isArchived": False,
                    "isExternallyManaged": True,
                    "externalMarketerId": None,
                    "internalMarketerId": None,
                    "amplifyReview": True,
                }
            ],
        )

    def test_list_filter_valid_modified_same_date(self, mock_modified_dt):
        ac1 = magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac1",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        mock_modified_dt.return_value = datetime.datetime(2019, 3, 3, 5, 10, 00)
        ac1.update(None, name="new name")

        url = reverse("service.salesforce.accounts")
        r = self.client.get(url, data={"modified_dt_start": "03-03-2019", "modified_dt_end": "30-03-2019"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            [
                {
                    "id": 2,
                    "name": "new name",
                    "agencyId": 3,
                    "salesforceUrl": None,
                    "salesforceId": 123,
                    "currency": "USD",
                    "salesRepresentative": None,
                    "accountManager": None,
                    "isDisabled": False,
                    "tags": [],
                    "customAttributes": {},
                    "modifiedDt": "03-03-2019",
                    "isArchived": False,
                    "isExternallyManaged": True,
                    "externalMarketerId": None,
                    "internalMarketerId": None,
                    "amplifyReview": True,
                }
            ],
        )

    def test_list_filter_valid_created_dt_start_inferior_created_dt_end(self, mock_modified_dt):
        magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac2",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        url = reverse("service.salesforce.accounts")
        r = self.client.get(url, data={"created_dt_start": "31-03-2019", "created_dt_end": "01-03-2019"})
        self.assertEqual(r.json(), [])

    def test_list_filter_invalid_date_format(self, mock_modified_dt):
        magic_mixer.blend(
            core.models.Account,
            id=2,
            name="ac2",
            agency=self.agency,
            salesforce_id=123,
            sales_representative=self.user,
            account_manager=self.user2,
        )
        url = reverse("service.salesforce.accounts")
        r = self.client.get(url, data={"created_dt_start": "2019-03-01", "created_dt_end": "2019-03-31"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(),
            {
                "errorCode": "ValidationError",
                "details": {
                    "createdDtStart": ["Date has wrong format. Use one of these formats instead: DD-MM-YYYY."],
                    "createdDtEnd": ["Date has wrong format. Use one of these formats instead: DD-MM-YYYY."],
                },
            },
        )

    def test_archive_valid(self, mock_modified_Dt):
        magic_mixer.blend(
            core.models.Account, agency=self.agency, id=1, name="Account 1", is_disabled=False, salesforce_id=123
        )

        url = reverse("service.salesforce.account.archive", kwargs={"account_id": 1})
        response = self.client.get(url)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": 1,
                    "name": "Account 1",
                    "agencyId": 3,
                    "salesforceUrl": None,
                    "salesforceId": 123,
                    "currency": "USD",
                    "salesRepresentative": None,
                    "accountManager": None,
                    "isDisabled": False,
                    "tags": [],
                    "customAttributes": {},
                    "modifiedDt": "02-03-2019",
                    "isArchived": True,
                    "isExternallyManaged": True,
                    "externalMarketerId": None,
                    "internalMarketerId": None,
                    "amplifyReview": True,
                }
            },
        )
