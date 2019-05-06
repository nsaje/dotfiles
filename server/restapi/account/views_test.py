from django.urls import reverse

import dash.models
import utils.test_helper
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AccountsTest(RESTAPITest):
    @classmethod
    def account_repr(
        cls,
        id=1,
        agency_id=1,
        name="My test account",
        archived=False,
        whitelist_publisher_groups=[153],
        blacklist_publisher_groups=[154],
        currency=dash.constants.Currency.USD,
        frequency_capping=None,
    ):
        representation = {
            "id": str(id),
            "agencyId": str(agency_id) if agency_id else None,
            "name": name,
            "archived": archived,
            "targeting": {
                "publisherGroups": {"included": whitelist_publisher_groups, "excluded": blacklist_publisher_groups}
            },
            "currency": currency,
            "frequencyCapping": frequency_capping,
        }
        return cls.normalize(representation)

    def validate_against_db(self, account):
        account_db = dash.models.Account.objects.get(pk=account["id"])
        settings_db = account_db.get_current_settings()
        expected = self.account_repr(
            id=account_db.id,
            agency_id=account_db.agency_id,
            name=settings_db.name,
            archived=settings_db.archived,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            currency=account_db.currency,
            frequency_capping=settings_db.frequency_capping,
        )
        self.assertEqual(expected, account)

    def test_accounts_list(self):
        r = self.client.get(reverse("accounts_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertGreater(len(resp_json["data"]), 0)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    # def test_accounts_list_exclude_archived(self):  # TODO: ARCHIVING
    #     self.user = magic_mixer.blend_request_user(permissions=["can_use_restapi", "can_set_frequency_capping"]).user
    #     self.client.force_authenticate(user=self.user)
    #     magic_mixer.cycle(3).blend(dash.models.Account, archived=False, users=[self.user])
    #     magic_mixer.cycle(2).blend(dash.models.Account, archived=True, users=[self.user])
    #     r = self.client.get(reverse("accounts_list"))
    #     resp_json = self.assertResponseValid(r, data_type=list)
    #     self.assertEqual(3, len(resp_json["data"]))
    #     for item in resp_json["data"]:
    #         self.validate_against_db(item)
    #         self.assertFalse(item["archived"])

    def test_accounts_list_include_archived(self):
        self.user = magic_mixer.blend_request_user(permissions=["can_use_restapi", "can_set_frequency_capping"]).user
        self.client.force_authenticate(user=self.user)
        magic_mixer.cycle(3).blend(dash.models.Account, archived=False, users=[self.user])
        magic_mixer.cycle(2).blend(dash.models.Account, archived=True, users=[self.user])
        r = self.client.get(reverse("accounts_list"), {"includeArchived": "TRUE"})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(5, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_accounts_post(self):
        new_account = self.account_repr(
            name="mytest",
            agency_id=1,
            whitelist_publisher_groups=[153, 154],
            blacklist_publisher_groups=[],
            frequency_capping=33,
        )
        del new_account["id"]
        self._test_accounts_post(new_account)

    def test_accounts_post_no_agency(self):
        new_account = self.account_repr(
            name="mytest", agency_id=None, whitelist_publisher_groups=[], blacklist_publisher_groups=[]
        )
        del new_account["id"]
        self._test_accounts_post(new_account)

    def test_accounts_post_no_agency_publisher_fail(self):
        new_account = self.account_repr(
            name="mytest", agency_id=None, whitelist_publisher_groups=[153, 154], blacklist_publisher_groups=[]
        )
        del new_account["id"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        new_account = self.account_repr(
            name="mytest", agency_id=None, whitelist_publisher_groups=[], blacklist_publisher_groups=[153, 154]
        )
        del new_account["id"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

    def _test_accounts_post(self, new_account):
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        self.assertEqual(resp_json["data"], new_account)

    def test_accounts_get(self):
        r = self.client.get(reverse("accounts_details", kwargs={"account_id": 186}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_account_get_permissionless(self):
        utils.test_helper.remove_permissions(self.user, permissions=["can_set_frequency_capping"])
        r = self.client.get(reverse("accounts_details", kwargs={"account_id": 186}))
        resp_json = self.assertResponseValid(r)
        self.assertFalse("frequencyCapping" in resp_json["data"])
        resp_json["data"]["frequencyCapping"] = None
        self.validate_against_db(resp_json["data"])

    def test_accounts_put(self):
        test_account = self.account_repr(
            id=186, whitelist_publisher_groups=[153, 154], blacklist_publisher_groups=[153, 154]
        )
        r = self.client.put(reverse("accounts_details", kwargs={"account_id": 186}), data=test_account, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"], test_account)

    def test_accounts_archive(self):
        self.user = magic_mixer.blend_request_user(permissions=["can_use_restapi", "can_set_frequency_capping"]).user
        self.client.force_authenticate(user=self.user)
        account = magic_mixer.blend(dash.models.Account, archived=False, users=[self.user])
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        self.assertFalse(account.is_archived())
        self.assertFalse(campaign.is_archived())

        test_account = self.account_repr(
            agency_id=None, id=account.id, archived=True, whitelist_publisher_groups=[], blacklist_publisher_groups=[]
        )
        r = self.client.put(
            reverse("accounts_details", kwargs={"account_id": account.id}), data=test_account, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"], test_account)
        account.refresh_from_db()
        campaign.refresh_from_db()
        self.assertTrue(account.is_archived())
        self.assertTrue(campaign.is_archived())

        test_account["archived"] = False
        r = self.client.put(
            reverse("accounts_details", kwargs={"account_id": account.id}), data=test_account, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"], test_account)
        account.refresh_from_db()
        campaign.refresh_from_db()
        self.assertFalse(account.is_archived())
        self.assertTrue(campaign.is_archived())

    def test_account_publisher_groups(self):
        test_account = self.account_repr(id=186, whitelist_publisher_groups=[153], blacklist_publisher_groups=[154])
        r = self.client.put(reverse("accounts_details", kwargs={"account_id": 186}), data=test_account, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        test_account = self.account_repr(id=186, whitelist_publisher_groups=[1])
        r = self.client.put(reverse("accounts_details", kwargs={"account_id": 186}), data=test_account, format="json")
        self.assertResponseError(r, "ValidationError")

        test_account = self.account_repr(id=186, blacklist_publisher_groups=[2])
        r = self.client.put(reverse("accounts_details", kwargs={"account_id": 186}), data=test_account, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_accounts_post_currency(self):
        new_account = self.account_repr(name="mytest", agency_id=1, currency=dash.constants.Currency.EUR)
        del new_account["id"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        self.assertEqual(resp_json["data"], new_account)
        self.assertEqual(resp_json["data"]["currency"], dash.constants.Currency.EUR)

        new_account = self.account_repr(name="mytest", agency_id=1)
        del new_account["id"]
        del new_account["currency"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        self.assertEqual(resp_json["data"]["currency"], dash.constants.Currency.USD)

        new_account = self.account_repr(name="mytest", agency_id=1, currency=None)
        del new_account["id"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        new_account = self.account_repr(name="mytest", agency_id=1, currency="")
        del new_account["id"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        new_account = self.account_repr(name="mytest", agency_id=1, currency=None)
        del new_account["id"]
        r = self.client.post(reverse("accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")
