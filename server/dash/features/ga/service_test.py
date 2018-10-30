import mock
from django.test import TestCase
from django.test import override_settings

from . import models
from . import service

ACCOUNTS_LIST_RESPONSE = {
    "username": "account-1@zemanta-api.iam.gserviceaccount.com",
    "kind": "analytics#accounts",
    "items": [
        {
            "kind": "analytics#account",
            "name": "WineAccess",
            "created": "2006-01-07T01:10:31.000Z",
            "updated": "2016-12-22T16:11:35.680Z",
            "childLink": {
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/214829/webproperties",
                "type": "analytics#webproperties",
            },
            "id": "111",
            "selfLink": "https://www.googleapis.com/analytics/v3/management/accounts/214829",
            "permissions": {"effective": ["READ_AND_ANALYZE"]},
        },
        {
            "kind": "analytics#account",
            "name": "Dermatology Associates of Plymouth Meeting, P.C.",
            "created": "2017-07-13T16:39:51.532Z",
            "updated": "2017-07-13T16:39:51.532Z",
            "childLink": {
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/102509553/webproperties",
                "type": "analytics#webproperties",
            },
            "id": "222",
            "selfLink": "https://www.googleapis.com/analytics/v3/management/accounts/102509553",
            "permissions": {"effective": []},
        },
    ],
    "itemsPerPage": 1000,
    "startIndex": 1,
    "totalResults": 2,
}

ACCOUNTS_LIST_RESPONSE_2 = {
    "username": "account-2@zemanta-api.iam.gserviceaccount.com",
    "kind": "analytics#accounts",
    "items": [
        {
            "kind": "analytics#account",
            "name": "WineAccess",
            "created": "2006-01-07T01:10:31.000Z",
            "updated": "2016-12-22T16:11:35.680Z",
            "childLink": {
                "href": "https://www.googleapis.com/analytics/v3/management/accounts/214829/webproperties",
                "type": "analytics#webproperties",
            },
            "id": "333",
            "selfLink": "https://www.googleapis.com/analytics/v3/management/accounts/214829",
            "permissions": {"effective": ["READ_AND_ANALYZE"]},
        }
    ],
    "itemsPerPage": 1000,
    "startIndex": 1,
    "totalResults": 1,
}


@override_settings(R1_DEMO_MODE=False)
@override_settings(GA_CREDENTIALS={"a-1@gapps.com": "password", "a-2@gapps.com": "password"})
class GALinkedAccountsTest(TestCase):
    def setUp(self):
        self.orig_services = service._management_services
        self.mock_services = {}
        service._management_services = self.mock_services

    def tearDown(self):
        service._management_services = self.orig_services

    def test_refresh_mappings(self):
        mock_1 = mock.Mock(name="mockservice1")
        mock_1.management().accounts().list().execute.return_value = ACCOUNTS_LIST_RESPONSE
        mock_2 = mock.Mock(name="mockservice2")
        mock_2.management().accounts().list().execute.return_value = ACCOUNTS_LIST_RESPONSE_2
        self.mock_services["a-1@gapps.com"] = mock_1
        self.mock_services["a-2@gapps.com"] = mock_2

        service.refresh_mappings()

        self.assertEqual(models.GALinkedAccounts.objects.count(), 3)
        self.assertTrue(
            models.GALinkedAccounts.objects.filter(
                customer_ga_account_id="111", zem_ga_account_email="a-1@gapps.com", has_read_and_analyze=True
            ).exists()
        )
        self.assertTrue(
            models.GALinkedAccounts.objects.filter(
                customer_ga_account_id="222", zem_ga_account_email="a-1@gapps.com", has_read_and_analyze=False
            ).exists()
        )
        self.assertTrue(
            models.GALinkedAccounts.objects.filter(
                customer_ga_account_id="333", zem_ga_account_email="a-2@gapps.com", has_read_and_analyze=True
            ).exists()
        )

    @mock.patch.object(service, "refresh_mappings")
    def test_is_readable_exists(self, mock_refresh_mappings):
        models.GALinkedAccounts.objects.create(
            customer_ga_account_id="444", zem_ga_account_email="a-1@gapps.com", has_read_and_analyze=True
        )
        self.assertTrue(service.is_readable("UA-444-3"))
        mock_refresh_mappings.assert_not_called()

    @mock.patch.object(service, "refresh_mappings")
    def test_is_readable_refresh(self, mock_refresh_mappings):
        models.GALinkedAccounts.objects.all().delete()
        mock_refresh_mappings.side_effect = lambda: models.GALinkedAccounts.objects.create(
            customer_ga_account_id="444", zem_ga_account_email="a-1@gapps.com", has_read_and_analyze=True
        )
        self.assertTrue(service.is_readable("UA-444-3"))
        mock_refresh_mappings.assert_called_once_with()

        self.assertFalse(service.is_readable("UA-555-3"))
