import mock
from django.urls import reverse

import core.models
import dash.constants
import utils.test_helper
from restapi.common.views_base_test_case import FutureRESTAPITestCase
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyAccountViewSetTest(RESTAPITestCase):
    @classmethod
    def account_repr(
        cls,
        id=None,
        agency_id=None,
        name="My test account",
        archived=False,
        whitelist_publisher_groups=[],
        blacklist_publisher_groups=[],
        currency=dash.constants.Currency.USD,
        frequency_capping=None,
    ):
        representation = {
            "id": str(id) if id else None,
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
        account_db = core.models.Account.objects.get(pk=account["id"])
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
        expected["defaultIconUrl"] = settings_db.get_base_default_icon_url() if settings_db.default_icon else None
        self.assertEqual(expected, account)

    def test_accounts_list(self):
        account_one = self.mix_account(user=self.user, permissions=[Permission.READ])
        account_two = self.mix_account(user=self.user, permissions=[Permission.READ])
        accounts_no_access = magic_mixer.cycle(5).blend(core.models.Account)
        r = self.client.get(reverse("restapi.account.v1:accounts_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = [x.get("id") for x in resp_json["data"]]
        self.assertTrue(str(account_one.id) in resp_json_ids)
        self.assertTrue(str(account_two.id) in resp_json_ids)
        for item in accounts_no_access:
            self.assertTrue(str(item.id) not in resp_json_ids)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_accounts_list_pagination(self):
        for i in range(10):
            self.mix_account(self.user, permissions=[Permission.READ])
        r = self.client.get(reverse("restapi.account.v1:accounts_list"))
        r_paginated = self.client.get(reverse("restapi.account.v1:accounts_list"), {"limit": 2, "offset": 5})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    def test_accounts_list_filter_by_agency_id(self):
        agency_one = self.mix_agency(user=self.user, permissions=[Permission.READ])
        magic_mixer.cycle(3).blend(core.models.Account, agency=agency_one)

        agency_two = self.mix_agency(user=self.user, permissions=[Permission.READ])
        magic_mixer.cycle(5).blend(core.models.Account, agency=agency_two)

        r = self.client.get(reverse("restapi.account.v1:accounts_list"), {"agencyId": agency_one.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 3)

    def test_accounts_list_filter_by_agency_id_with_account_access(self):
        agency = magic_mixer.blend(core.models.Agency)

        self.mix_account(self.user, permissions=[Permission.READ], agency=agency)
        self.mix_account(self.user, permissions=[Permission.READ], agency=agency)
        self.mix_account(self.user, permissions=[Permission.READ], agency=agency)

        magic_mixer.cycle(5).blend(core.models.Account, agency=agency)

        r = self.client.get(reverse("restapi.account.v1:accounts_list"), {"agencyId": agency.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 3)

    def test_accounts_list_filter_by_agency_id_with_agency_access(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(5).blend(core.models.Account, agency=agency)

        r = self.client.get(reverse("restapi.account.v1:accounts_list"), {"agencyId": agency.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 5)

    def test_accounts_list_exclude_archived(self):
        agency = self.mix_agency(user=self.user, permissions=[Permission.READ])
        non_arhived_accounts = magic_mixer.cycle(3).blend(core.models.Account, agency=agency, archived=False)
        arhived_accounts = magic_mixer.cycle(2).blend(core.models.Account, agency=agency, archived=True)
        r = self.client.get(reverse("restapi.account.v1:accounts_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = [x.get("id") for x in resp_json["data"]]
        for item in non_arhived_accounts:
            self.assertTrue(str(item.id) in resp_json_ids)
        for item in arhived_accounts:
            self.assertTrue(str(item.id) not in resp_json_ids)
        for item in resp_json["data"]:
            item["defaultIconUrl"] = None
            self.validate_against_db(item)
            self.assertFalse(item["archived"])

    def test_accounts_list_include_archived(self):
        agency = self.mix_agency(user=self.user, permissions=[Permission.READ])
        non_arhived_accounts = magic_mixer.cycle(3).blend(core.models.Account, agency=agency, archived=False)
        arhived_accounts = magic_mixer.cycle(2).blend(core.models.Account, agency=agency, archived=True)
        r = self.client.get(reverse("restapi.account.v1:accounts_list"), {"includeArchived": "TRUE"})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = [x.get("id") for x in resp_json["data"]]
        for item in non_arhived_accounts:
            self.assertTrue(str(item.id) in resp_json_ids)
        for item in arhived_accounts:
            self.assertTrue(str(item.id) in resp_json_ids)
        for item in resp_json["data"]:
            item["defaultIconUrl"] = None
            self.validate_against_db(item)

    def test_accounts_post(self):
        agency = self.mix_agency(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)

        new_account = self.account_repr(
            name="mytest",
            agency_id=agency.id,
            whitelist_publisher_groups=[pg_one.id, pg_two.id],
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
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        new_account = self.account_repr(
            name="mytest", agency_id=None, whitelist_publisher_groups=[], blacklist_publisher_groups=[153, 154]
        )
        del new_account["id"]
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

    def _test_accounts_post(self, new_account):
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        new_account["defaultIconUrl"] = None
        self.assertEqual(resp_json["data"], new_account)

    def test_accounts_get(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        r = self.client.get(reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_account_get_permissionless(self):
        utils.test_helper.remove_permissions(self.user, permissions=["can_set_frequency_capping"])
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        r = self.client.get(reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)
        self.assertFalse("frequencyCapping" in resp_json["data"])
        resp_json["data"]["frequencyCapping"] = None
        self.validate_against_db(resp_json["data"])

    def test_accounts_put(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)

        test_account = self.account_repr(
            id=account.id, whitelist_publisher_groups=[pg_one.id], blacklist_publisher_groups=[pg_two.id]
        )
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}),
            data=test_account,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        test_account["defaultIconUrl"] = None
        self.assertEqual(resp_json["data"], test_account)

    def test_accounts_archive(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ, Permission.WRITE], archived=False)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        self.assertFalse(account.is_archived())
        self.assertFalse(campaign.is_archived())

        test_account = self.account_repr(
            id=account.id, archived=True, whitelist_publisher_groups=[], blacklist_publisher_groups=[]
        )
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}),
            data=test_account,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        test_account["defaultIconUrl"] = None
        self.assertEqual(resp_json["data"], test_account)
        del test_account["defaultIconUrl"]
        account.refresh_from_db()
        campaign.refresh_from_db()
        self.assertTrue(account.is_archived())
        self.assertTrue(campaign.is_archived())

        test_account["archived"] = False
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}),
            data=test_account,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        test_account["defaultIconUrl"] = None
        self.assertEqual(resp_json["data"], test_account)
        account.refresh_from_db()
        campaign.refresh_from_db()
        self.assertFalse(account.is_archived())
        self.assertTrue(campaign.is_archived())

    def test_account_publisher_groups(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)

        test_account = self.account_repr(
            id=account.id, whitelist_publisher_groups=[pg_one.id], blacklist_publisher_groups=[pg_two.id]
        )
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}),
            data=test_account,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        test_account = self.account_repr(id=account.id, whitelist_publisher_groups=[-1])
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}),
            data=test_account,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        test_account = self.account_repr(id=account.id, blacklist_publisher_groups=[-1])
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}),
            data=test_account,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_accounts_post_currency(self):
        agency = self.mix_agency(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        new_account = self.account_repr(name="mytest", agency_id=agency.id, currency=dash.constants.Currency.EUR)
        del new_account["id"]
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        new_account["defaultIconUrl"] = None
        self.assertEqual(resp_json["data"], new_account)
        self.assertEqual(resp_json["data"]["currency"], dash.constants.Currency.EUR)

        new_account = self.account_repr(name="mytest", agency_id=agency.id)
        del new_account["id"]
        del new_account["currency"]
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        self.assertEqual(resp_json["data"]["currency"], dash.constants.Currency.USD)

        new_account = self.account_repr(name="mytest", agency_id=agency.id, currency=None)
        del new_account["id"]
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        new_account = self.account_repr(name="mytest", agency_id=agency.id, currency="")
        del new_account["id"]
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        new_account = self.account_repr(name="mytest", agency_id=agency.id, currency=None)
        del new_account["id"]
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_accounts_get_default_icon(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", image_hash="icon_hash", width=150, height=150, file_size=1000
        )
        account.settings.update_unsafe(None, default_icon=default_icon)
        r = self.client.get(reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])
        self.assertEqual(resp_json["data"]["defaultIconUrl"], account.settings.get_base_default_icon_url())

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_accounts_put_default_icon(self, mock_external_validation, mock_s3_upload, _):
        account = self.mix_account(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://icon.url.com": {
                        "valid": True,
                        "id": "icon_id",
                        "hash": "icon_hash",
                        "width": 180,
                        "height": 180,
                        "file_size": 1000,
                    }
                }
            },
        }
        data = {"default_icon_url": "http://icon.url.com"}
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        account.refresh_from_db()
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(180, account.settings.default_icon.width)
        self.assertEqual(180, account.settings.default_icon.height)
        self.assertEqual(1000, account.settings.default_icon.file_size)
        self.assertEqual("http://icon.url.com", account.settings.default_icon.origin_url)

        mock_s3_upload.assert_not_called()

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_accounts_put_default_icon_fail(self, mock_external_validation, mock_s3_upload, _):
        account = self.mix_account(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://icon.url.com": {
                        "valid": False,
                        "id": "icon_id",
                        "hash": "icon_hash",
                        "width": 150,
                        "height": 150,
                        "file_size": 1000,
                    }
                }
            },
        }
        data = {"default_icon_url": "http://icon.url.com"}
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["valid"] = True
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["id"] = None
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["id"] = "icon_id"
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 151
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 127
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["height"] = 127
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 10001
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["height"] = 10001
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 128
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["height"] = 128
        r = self.client.put(
            reverse("restapi.account.v1:accounts_details", kwargs={"account_id": account.id}), data=data, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        account.refresh_from_db()
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(128, account.settings.default_icon.width)
        self.assertEqual(128, account.settings.default_icon.height)
        self.assertEqual(1000, account.settings.default_icon.file_size)
        self.assertEqual("http://icon.url.com", account.settings.default_icon.origin_url)

        mock_s3_upload.assert_not_called()

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_accounts_post_default_icon(self, mock_external_validation, mock_s3_upload, _):
        agency = self.mix_agency(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://icon.url.com": {
                        "valid": True,
                        "id": "icon_id",
                        "hash": "icon_hash",
                        "width": 170,
                        "height": 170,
                        "file_size": 2000,
                    }
                }
            },
        }
        new_account = self.account_repr(
            name="mytest",
            agency_id=agency.id,
            whitelist_publisher_groups=[pg_one.id, pg_two.id],
            blacklist_publisher_groups=[],
            frequency_capping=33,
        )
        del new_account["id"]
        new_account["defaultIconUrl"] = "http://icon.url.com"
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        new_account["defaultIconUrl"] = resp_json["data"]["defaultIconUrl"]
        self.assertEqual(resp_json["data"], new_account)
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])

        account = core.models.Account.objects.get(id=new_account["id"])
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(170, account.settings.default_icon.width)
        self.assertEqual(170, account.settings.default_icon.height)
        self.assertEqual(2000, account.settings.default_icon.file_size)
        self.assertEqual("http://icon.url.com", account.settings.default_icon.origin_url)

        mock_s3_upload.assert_not_called()

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_accounts_post_default_icon_fail(self, mock_external_validation, mock_s3_upload, _):
        agency = self.mix_agency(user=self.user, permissions=[Permission.READ, Permission.WRITE])
        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        new_account = self.account_repr(
            name="mytest",
            agency_id=agency.id,
            whitelist_publisher_groups=[pg_one.id, pg_two.id],
            blacklist_publisher_groups=[],
            frequency_capping=33,
        )
        del new_account["id"]
        new_account["defaultIconUrl"] = "http://icon.url.com"

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://icon.url.com": {
                        "valid": False,
                        "id": "icon_id",
                        "hash": "icon_hash",
                        "width": 170,
                        "height": 170,
                        "file_size": 2000,
                    }
                }
            },
        }
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["valid"] = True
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["id"] = None
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["id"] = "icon_id"
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 151
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 127
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["height"] = 127
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 10001
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["height"] = 10001
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["width"] = 128
        mock_external_validation.return_value["candidate"]["images"]["http://icon.url.com"]["height"] = 128
        r = self.client.post(reverse("restapi.account.v1:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_account["id"] = resp_json["data"]["id"]
        new_account["defaultIconUrl"] = resp_json["data"]["defaultIconUrl"]
        self.assertEqual(resp_json["data"], new_account)
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])

        account = core.models.Account.objects.get(id=new_account["id"])
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(128, account.settings.default_icon.width)
        self.assertEqual(128, account.settings.default_icon.height)
        self.assertEqual(2000, account.settings.default_icon.file_size)
        self.assertEqual("http://icon.url.com", account.settings.default_icon.origin_url)

        mock_s3_upload.assert_not_called()


class AccountViewSetTest(FutureRESTAPITestCase, LegacyAccountViewSetTest):
    pass
