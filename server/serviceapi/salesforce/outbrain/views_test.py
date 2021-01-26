import datetime

import mock
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

import core.models
import zemauth.models
from utils.magic_mixer import magic_mixer
from zemauth.models import User

from . import constants


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
        self.user = magic_mixer.blend(User, email="salesRep@test.com", is_externally_managed=True, sales_office="USBIZ")
        self.user2 = magic_mixer.blend(
            User, email="accountManager@test.com", is_externally_managed=True, sales_office="USBIZ"
        )
        self.aguser = magic_mixer.blend(
            User, email="agencysalesrep@test.com", is_externally_managed=True, sales_office="USBIZ"
        )
        self.aguser2 = magic_mixer.blend(
            User, email="agencyaccountmgr@test.com", is_externally_managed=True, sales_office="USBIZ"
        )
        self.outbrainAgencyUser = magic_mixer.blend(
            User, email="OutbrainAgencyUser@test.com", is_externally_managed=True, sales_office="USBIZ"
        )
        self.notInMappingUser = magic_mixer.blend(
            User, email="notInMapping@test.com", is_externally_managed=True, sales_office="ABCD"
        )
        self.client.force_authenticate(user=self.service_user)
        self.request_mock = RequestFactory()
        self.request_mock.user = self.service_user

        self.agency = magic_mixer.blend(
            core.models.Agency, id=3, name="Agency 1", is_externally_managed=True, sales_representative=self.aguser
        )
        self.video_agency = magic_mixer.blend(
            core.models.Agency, id=221, name="video Agency", is_externally_managed=True
        )
        self.Outbrain_unknown_Agency = magic_mixer.blend(
            core.models.Agency, id=517, name="Outbrain ZMS Unknown", is_externally_managed=True
        )

        constants.SALES_OFFICE_AGENCY_MAPPING = {"USBIZ": 3}

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

    # TODO jh uncomment after out of hybrid mode
    # def test_post_with_sales_rep_not_in_mapping(self, mock_modified_dt):
    #     url = reverse("service.salesforce.account")
    #     r = self.client.post(
    #         url,
    #         data={
    #             "is_disabled": True,
    #             "name": "new Account",
    #             "salesforce_url": "http://salesforce.com",
    #             "currency": "CHF",
    #             "sales_representative": "notInMapping@test.com",
    #             "account_manager": "accountManager@test.com",
    #             "tags": ["tag1", "tag2"],
    #             "custom_attributes": {"country": "SI"},
    #             "salesforce_id": 123,
    #             "internal_marketer_id": "INTERNAL ID",
    #             "external_marketer_id": "EXTERNAL ID",
    #         },
    #         format="json",
    #     )

    #     self.assertEqual(r.status_code, 400)
    #     new_account = core.models.Account.objects.filter(name="new Account").first()
    #     self.assertIsNone(new_account)
    #     self.assertEqual(
    #         r.json(), {"errorCode": "ValidationError", "details": ["Agency for this sales office doesn't exist"]}
    #     )

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


class UserTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.service_user = magic_mixer.blend(User, email="outbrain-salesforce@service.zemanta.com")
        self.client.force_authenticate(user=self.service_user)
        self.request_mock = RequestFactory()
        constants.SALES_OFFICE_AGENCY_MAPPING = {"USBIZ": 1, "Spain": 2}

    def test_get_valid(self):
        magic_mixer.blend(
            zemauth.models.User,
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=True,
        )

        url = reverse("service.salesforce.user", kwargs={"user_id": 1})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": 1,
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john@doe.com",
                    "salesOffice": "USBIZ",
                }
            },
        )

    def test_get_invalid_is_not_externally_managed(self):
        magic_mixer.blend(
            zemauth.models.User,
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=False,
        )

        url = reverse("service.salesforce.user", kwargs={"user_id": 1})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {"errorCode": "DoesNotExist", "details": "User matching query does not exist."})

    def test_get_invalid_does_not_exist(self):
        url = reverse("service.salesforce.user", kwargs={"user_id": 1234})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {"errorCode": "DoesNotExist", "details": "User matching query does not exist."})

    @mock.patch("utils.email_helper.send_unknown_sales_office_email")
    def test_post_valid(self, send_email_mock):
        url = reverse("service.salesforce.user")
        r = self.client.post(
            url,
            data={"email": "john@doe.com", "first_name": "John", "last_name": "Doe", "sales_office": "USBIZ"},
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        user = zemauth.models.User.objects.filter(email__iexact="john@doe.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": user.id,
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john@doe.com",
                    "salesOffice": "USBIZ",
                }
            },
        )
        send_email_mock.assert_not_called()

    @mock.patch("utils.email_helper.send_unknown_sales_office_email")
    def test_post_valid_unkown_sales_office(self, send_email_mock):
        url = reverse("service.salesforce.user")
        r = self.client.post(
            url,
            data={"email": "john@doe.com", "first_name": "John", "last_name": "Doe", "sales_office": "ABCD"},
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        user = zemauth.models.User.objects.filter(email__iexact="john@doe.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": user.id,
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john@doe.com",
                    "salesOffice": "ABCD",
                }
            },
        )
        send_email_mock.assert_called_once()

    def test_post_invalid_email_exists(self):
        magic_mixer.blend(
            zemauth.models.User,
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=True,
        )

        url = reverse("service.salesforce.user")
        r = self.client.post(
            url,
            data={"email": "john@doe.com", "first_name": "John", "last_name": "Doe", "sales_office": "USBIZ"},
            format="json",
        )

        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"errorCode": "ValidationError", "details": {"email": ["User with this email already exists."]}}
        )

    @mock.patch("utils.email_helper.send_unknown_sales_office_email")
    def test_put_valid(self, send_email_mock):
        magic_mixer.blend(
            zemauth.models.User,
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=True,
        )

        url = reverse("service.salesforce.user", kwargs={"user_id": 1})
        r = self.client.put(
            url,
            data={"email": "jane@deen.com", "first_name": "Jane", "last_name": "Deen", "sales_office": "Spain"},
            format="json",
        )

        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": 1,
                    "email": "jane@deen.com",
                    "firstName": "Jane",
                    "lastName": "Deen",
                    "salesOffice": "Spain",
                }
            },
        )
        send_email_mock.assert_not_called()

    @mock.patch("utils.email_helper.send_unknown_sales_office_email")
    def test_put_valid_unkown_sales_office(self, send_email_mock):
        magic_mixer.blend(
            zemauth.models.User,
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=True,
        )

        url = reverse("service.salesforce.user", kwargs={"user_id": 1})
        r = self.client.put(url, data={"sales_office": "ABCD"}, format="json")

        self.assertEqual(r.status_code, 200)
        user = zemauth.models.User.objects.filter(email__iexact="john@doe.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": user.id,
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john@doe.com",
                    "salesOffice": "ABCD",
                }
            },
        )
        send_email_mock.assert_called_once()

    def test_put_invalid_email_exists(self):
        magic_mixer.blend(
            zemauth.models.User,
            id=1,
            first_name="John",
            last_name="Doe",
            email="john@doe.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=True,
        )
        magic_mixer.blend(
            zemauth.models.User,
            id=2,
            first_name="Jane",
            last_name="Deen",
            email="jane@deen.com",
            is_active=True,
            sales_office="USBIZ",
            is_externally_managed=True,
        )

        url = reverse("service.salesforce.user", kwargs={"user_id": 1})
        r = self.client.put(url, data={"email": "jane@deen.com"}, format="json")

        self.assertEqual(r.status_code, 400)
        self.assertEqual(
            r.json(), {"errorCode": "ValidationError", "details": {"email": ["User with this email already exists."]}}
        )

    def test_put_invalid_does_not_exist(self):
        url = reverse("service.salesforce.user", kwargs={"user_id": 1234})
        r = self.client.put(url)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json(), {"errorCode": "DoesNotExist", "details": "User matching query does not exist."})

    def test_get_all(self):
        magic_mixer.cycle(3).blend(zemauth.models.User, is_externally_managed=True)
        magic_mixer.cycle(4).blend(zemauth.models.User, is_externally_managed=False)
        url = reverse("service.salesforce.users")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 3)

    def test_get_all_email_filter(self):
        magic_mixer.cycle(3).blend(zemauth.models.User, is_externally_managed=True)
        magic_mixer.cycle(4).blend(zemauth.models.User, is_externally_managed=False)
        magic_mixer.blend(zemauth.models.User, email="new@doe.com", is_externally_managed=True)
        url = reverse("service.salesforce.users")
        r = self.client.get(url, data={"email": "new@doe.com"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)
