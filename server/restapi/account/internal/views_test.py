import mock
from django.urls import reverse

import core.features.deals
import core.models
import dash.constants
from restapi.common.views_base_test import RESTAPITest
from utils import test_helper
from utils.magic_mixer import magic_mixer


class AccountViewSetTest(RESTAPITest):
    @classmethod
    def account_repr(
        cls,
        account_id=None,
        agency_id=None,
        account_name=None,
        archived=False,
        currency=dash.constants.Currency.USD,
        frequency_capping=None,
        account_type=dash.constants.AccountType.UNKNOWN,
        default_account_manager=None,
        default_sales_representative=None,
        default_cs_representative=None,
        ob_sales_representative=None,
        ob_account_manager=None,
        auto_add_new_sources=None,
        salesforce_url=None,
        allowed_media_sources=[],
        deals=[],
        default_icon_url=None,
        default_icon_base64=None,
    ):
        representation = {
            "id": str(account_id) if account_id is not None else None,
            "agencyId": str(agency_id) if agency_id is not None else None,
            "targeting": {"publisherGroups": {"included": [], "excluded": []}},
            "name": account_name,
            "archived": archived,
            "currency": dash.constants.Currency.get_name(currency),
            "frequencyCapping": frequency_capping,
            "accountType": dash.constants.AccountType.get_name(account_type),
            "defaultAccountManager": str(default_account_manager) if default_account_manager is not None else None,
            "defaultSalesRepresentative": str(default_sales_representative)
            if default_sales_representative is not None
            else None,
            "defaultCsRepresentative": str(default_cs_representative)
            if default_cs_representative is not None
            else None,
            "obSalesRepresentative": str(ob_sales_representative) if ob_sales_representative is not None else None,
            "obAccountManager": str(ob_account_manager) if ob_account_manager is not None else None,
            "autoAddNewSources": auto_add_new_sources,
            "salesforceUrl": salesforce_url,
            "allowedMediaSources": allowed_media_sources,
            "deals": deals,
            "defaultIconUrl": default_icon_url,
            "defaultIconBase64": default_icon_base64,
        }
        return cls.normalize(representation)

    def test_validate_empty(self):
        r = self.client.post(reverse("restapi.account.internal:accounts_validate"))
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {"name": "New account"}
        r = self.client.post(reverse("restapi.account.internal:accounts_validate"), data=data, format="json")
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"name": None}
        r = self.client.post(reverse("restapi.account.internal:accounts_validate"), data=data, format="json")
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["name"][0])

    @mock.patch("restapi.account.internal.helpers.get_extra_data")
    def test_get_default(self, mock_get_extra_data):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        mock_get_extra_data.return_value = {
            "archived": False,
            "can_archive": True,
            "can_restore": True,
            "is_externally_managed": False,
            "agencies": [
                {
                    "id": 123,
                    "name": "agency",
                    "sales_representative": 1,
                    "cs_representative": 2,
                    "ob_sales_representative": 3,
                    "ob_account_manager": 4,
                    "default_account_type": dash.constants.AccountType.UNKNOWN,
                }
            ],
            "account_managers": [
                {"id": 100, "name": "manager1@outbrain.com"},
                {"id": 101, "name": "manager2@outbrain.com"},
            ],
            "sales_representatives": [
                {"id": 110, "name": "sales1@outbrain.com"},
                {"id": 111, "name": "sales2@outbrain.com"},
            ],
            "cs_representatives": [{"id": 200, "name": "cs1@outbrain.com"}, {"id": 201, "name": "cs2@outbrain.com"}],
            "ob_representatives": [
                {"id": 220, "name": "ob1@outbrain.com"},
                {"id": 222, "name": "ob2@outbrain.com"},
                {"id": 221, "name": "ob2@outbrain.com"},
                {"id": 223, "name": "ob3@outbrain.com"},
            ],
            "hacks": [],
            "deals": [],
            "available_media_sources": [
                {
                    "id": str(sources[0].id),
                    "name": sources[0].name,
                    "released": sources[0].released,
                    "deprecated": sources[0].deprecated,
                },
                {
                    "id": str(sources[1].id),
                    "name": sources[1].name,
                    "released": sources[1].released,
                    "deprecated": sources[1].deprecated,
                },
                {
                    "id": str(sources[2].id),
                    "name": sources[2].name,
                    "released": sources[2].released,
                    "deprecated": sources[2].deprecated,
                },
            ],
        }

        r = self.client.get(reverse("restapi.account.internal:accounts_defaults"))
        resp_json = self.assertResponseValid(r)

        self.assertIsNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["agencyId"], str(agency.id))
        self.assertEqual(resp_json["data"]["name"], "")
        self.assertEqual(
            resp_json["data"]["accountType"], dash.constants.AccountType.get_name(dash.constants.AccountType.ACTIVATED)
        )
        self.assertEqual(resp_json["data"]["defaultAccountManager"], str(self.user.id))
        self.assertEqual(
            resp_json["data"]["defaultSalesRepresentative"],
            str(agency.sales_representative.id) if agency.sales_representative is not None else None,
        )
        self.assertEqual(
            resp_json["data"]["defaultCsRepresentative"],
            str(agency.cs_representative.id) if agency.cs_representative is not None else None,
        )
        self.assertEqual(
            resp_json["data"]["obSalesRepresentative"],
            str(agency.ob_sales_representative.id) if agency.ob_sales_representative is not None else None,
        )
        self.assertEqual(
            resp_json["data"]["obAccountManager"],
            str(agency.ob_account_manager.id) if agency.ob_account_manager is not None else None,
        )
        self.assertEqual(resp_json["data"]["autoAddNewSources"], True)
        self.assertEqual(resp_json["data"]["salesforceUrl"], "")

        self.assertEqual(len(resp_json["data"]["allowedMediaSources"]), 3)
        self.assertEqual(resp_json["data"]["allowedMediaSources"][0]["id"], str(sources[0].id))
        self.assertEqual(resp_json["data"]["allowedMediaSources"][1]["id"], str(sources[1].id))
        self.assertEqual(resp_json["data"]["allowedMediaSources"][2]["id"], str(sources[2].id))

        self.assertEqual(resp_json["data"]["deals"], [])

        self.assertEqual(
            resp_json["extra"],
            {
                "archived": False,
                "canArchive": True,
                "canRestore": True,
                "isExternallyManaged": False,
                "agencies": [
                    {
                        "id": "123",
                        "name": "agency",
                        "salesRepresentative": "1",
                        "csRepresentative": "2",
                        "obSalesRepresentative": "3",
                        "obAccountManager": "4",
                        "defaultAccountType": dash.constants.AccountType.get_name(dash.constants.AccountType.UNKNOWN),
                    }
                ],
                "accountManagers": [
                    {"id": "100", "name": "manager1@outbrain.com"},
                    {"id": "101", "name": "manager2@outbrain.com"},
                ],
                "salesRepresentatives": [
                    {"id": "110", "name": "sales1@outbrain.com"},
                    {"id": "111", "name": "sales2@outbrain.com"},
                ],
                "csRepresentatives": [
                    {"id": "200", "name": "cs1@outbrain.com"},
                    {"id": "201", "name": "cs2@outbrain.com"},
                ],
                "obRepresentatives": [
                    {"id": "220", "name": "ob1@outbrain.com"},
                    {"id": "222", "name": "ob2@outbrain.com"},
                    {"id": "221", "name": "ob2@outbrain.com"},
                    {"id": "223", "name": "ob3@outbrain.com"},
                ],
                "hacks": [],
                "deals": [],
                "availableMediaSources": [
                    {
                        "id": str(sources[0].id),
                        "name": sources[0].name,
                        "released": sources[0].released,
                        "deprecated": sources[0].deprecated,
                    },
                    {
                        "id": str(sources[1].id),
                        "name": sources[1].name,
                        "released": sources[1].released,
                        "deprecated": sources[1].deprecated,
                    },
                    {
                        "id": str(sources[2].id),
                        "name": sources[2].name,
                        "released": sources[2].released,
                        "deprecated": sources[2].deprecated,
                    },
                ],
            },
        )

    @mock.patch("restapi.account.internal.helpers.get_extra_data")
    def test_get(self, mock_get_extra_data):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        default_icon = magic_mixer.blend(
            core.models.ImageAsset, image_id="icon_id", image_hash="icon_hash", width=150, height=150, file_size=1000
        )
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_sales_representative=None,
            ob_account_manager=None,
            auto_add_new_sources=True,
            salesforce_url="Generic URL",
            default_icon=default_icon,
        )

        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list(sources))
        account.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=sources[0])
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account)

        mock_get_extra_data.return_value = {
            "archived": False,
            "can_archive": True,
            "can_restore": True,
            "is_externally_managed": False,
            "agencies": [
                {
                    "id": 123,
                    "name": "agency",
                    "sales_representative": 1,
                    "cs_representative": 2,
                    "ob_sales_representative": 3,
                    "ob_account_manager": 4,
                    "default_account_type": dash.constants.AccountType.UNKNOWN,
                }
            ],
            "account_managers": [
                {"id": 100, "name": "manager1@outbrain.com"},
                {"id": 101, "name": "manager2@outbrain.com"},
            ],
            "sales_representatives": [
                {"id": 110, "name": "sales1@outbrain.com"},
                {"id": 111, "name": "sales2@outbrain.com"},
            ],
            "cs_representatives": [{"id": 200, "name": "cs1@outbrain.com"}, {"id": 201, "name": "cs2@outbrain.com"}],
            "ob_representatives": [
                {"id": 220, "name": "ob1@outbrain.com"},
                {"id": 222, "name": "ob2@outbrain.com"},
                {"id": 220, "name": "ob1@outbrain.com"},
                {"id": 222, "name": "ob2@outbrain.com"},
            ],
            "hacks": [],
            "deals": [],
            "available_media_sources": [
                {
                    "id": str(sources[0].id),
                    "name": sources[0].name,
                    "released": sources[0].released,
                    "deprecated": sources[0].deprecated,
                },
                {
                    "id": str(sources[1].id),
                    "name": sources[1].name,
                    "released": sources[1].released,
                    "deprecated": sources[1].deprecated,
                },
                {
                    "id": str(sources[2].id),
                    "name": sources[2].name,
                    "released": sources[2].released,
                    "deprecated": sources[2].deprecated,
                },
                {
                    "id": str(sources[3].id),
                    "name": sources[3].name,
                    "released": sources[3].released,
                    "deprecated": sources[3].deprecated,
                },
                {
                    "id": str(sources[4].id),
                    "name": sources[4].name,
                    "released": sources[4].released,
                    "deprecated": sources[4].deprecated,
                },
            ],
        }

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(account.id))
        self.assertEqual(resp_json["data"]["agencyId"], str(account.agency.id))
        self.assertEqual(resp_json["data"]["name"], account.settings.name)
        self.assertEqual(
            resp_json["data"]["accountType"], dash.constants.AccountType.get_name(account.settings.account_type)
        )
        self.assertEqual(
            resp_json["data"]["defaultAccountManager"],
            str(account.settings.default_account_manager.id)
            if account.settings.default_account_manager is not None
            else None,
        )
        self.assertEqual(
            resp_json["data"]["defaultSalesRepresentative"],
            str(account.settings.default_sales_representative.id)
            if account.settings.default_sales_representative is not None
            else None,
        )
        self.assertEqual(
            resp_json["data"]["defaultCsRepresentative"],
            str(account.settings.default_cs_representative.id)
            if account.settings.default_cs_representative is not None
            else None,
        )
        self.assertEqual(
            resp_json["data"]["obSalesRepresentative"],
            str(account.settings.ob_sales_representative.id)
            if account.settings.ob_sales_representative is not None
            else None,
        )
        self.assertEqual(
            resp_json["data"]["obAccountManager"],
            str(account.settings.ob_account_manager.id) if account.settings.ob_account_manager is not None else None,
        )
        self.assertEqual(resp_json["data"]["autoAddNewSources"], account.settings.auto_add_new_sources)
        self.assertEqual(resp_json["data"]["salesforceUrl"], account.settings.salesforce_url)
        self.assertEqual(
            resp_json["data"]["allowedMediaSources"],
            [
                {
                    "id": str(sources[0].id),
                    "name": sources[0].name,
                    "released": sources[0].released,
                    "deprecated": sources[0].deprecated,
                },
                {
                    "id": str(sources[1].id),
                    "name": sources[1].name,
                    "released": sources[1].released,
                    "deprecated": sources[1].deprecated,
                },
                {
                    "id": str(sources[2].id),
                    "name": sources[2].name,
                    "released": sources[2].released,
                    "deprecated": sources[2].deprecated,
                },
            ],
        )
        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["defaultIconUrl"], account.settings.get_base_default_icon_url())

        self.assertEqual(
            resp_json["extra"],
            {
                "archived": False,
                "canArchive": True,
                "canRestore": True,
                "isExternallyManaged": False,
                "agencies": [
                    {
                        "id": "123",
                        "name": "agency",
                        "salesRepresentative": "1",
                        "csRepresentative": "2",
                        "obSalesRepresentative": "3",
                        "obAccountManager": "4",
                        "defaultAccountType": dash.constants.AccountType.get_name(dash.constants.AccountType.UNKNOWN),
                    }
                ],
                "accountManagers": [
                    {"id": "100", "name": "manager1@outbrain.com"},
                    {"id": "101", "name": "manager2@outbrain.com"},
                ],
                "salesRepresentatives": [
                    {"id": "110", "name": "sales1@outbrain.com"},
                    {"id": "111", "name": "sales2@outbrain.com"},
                ],
                "csRepresentatives": [
                    {"id": "200", "name": "cs1@outbrain.com"},
                    {"id": "201", "name": "cs2@outbrain.com"},
                ],
                "obRepresentatives": [
                    {"id": "220", "name": "ob1@outbrain.com"},
                    {"id": "222", "name": "ob2@outbrain.com"},
                    {"id": "220", "name": "ob1@outbrain.com"},
                    {"id": "222", "name": "ob2@outbrain.com"},
                ],
                "hacks": [],
                "deals": [],
                "availableMediaSources": [
                    {
                        "id": str(sources[0].id),
                        "name": sources[0].name,
                        "released": sources[0].released,
                        "deprecated": sources[0].deprecated,
                    },
                    {
                        "id": str(sources[1].id),
                        "name": sources[1].name,
                        "released": sources[1].released,
                        "deprecated": sources[1].deprecated,
                    },
                    {
                        "id": str(sources[2].id),
                        "name": sources[2].name,
                        "released": sources[2].released,
                        "deprecated": sources[2].deprecated,
                    },
                    {
                        "id": str(sources[3].id),
                        "name": sources[3].name,
                        "released": sources[3].released,
                        "deprecated": sources[3].deprecated,
                    },
                    {
                        "id": str(sources[4].id),
                        "name": sources[4].name,
                        "released": sources[4].released,
                        "deprecated": sources[4].deprecated,
                    },
                ],
            },
        )

    @mock.patch("restapi.account.internal.helpers.get_extra_data")
    def test_get_internal_deals_no_permission(self, mock_get_extra_data):
        account = magic_mixer.blend(core.models.Account, name="Generic account", users=[self.user])
        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source, is_internal=True)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account)

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(len(resp_json["data"]["deals"]), 0)

    @mock.patch("restapi.account.internal.helpers.get_extra_data")
    def test_get_internal_deals_permission(self, mock_get_extra_data):
        account = magic_mixer.blend(core.models.Account, name="Generic account", users=[self.user])
        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source, is_internal=True)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account)

        test_helper.add_permissions(self.user, ["can_see_internal_deals"])
        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 1)

    @mock.patch("utils.slack.publish")
    def test_put(self, mock_slack_publish):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user], id=1)
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_sales_representative=None,
            ob_account_manager=None,
            auto_add_new_sources=True,
            salesforce_url="http://salesforce.com",
        )

        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list(sources))
        account_allowed_sources = [sources[0], sources[1], sources[2]]
        account.allowed_sources.add(*list(account_allowed_sources))

        deal_to_be_removed = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=sources[0])
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal_to_be_removed, account=account)

        deal_to_be_added = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=sources[1])

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["allowedMediaSources"]), 3)
        account_allowed_sources_ids = [str(s.id) for s in account_allowed_sources]
        for i in range(3):
            self.assertIn(resp_json["data"]["allowedMediaSources"][i]["id"], account_allowed_sources_ids)

        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal_to_be_removed.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)

        put_data = resp_json["data"].copy()

        put_data["name"] = "New generic account"
        put_data["salesforceUrl"] = "http://salesforce2.com"
        put_data["autoAddNewSources"] = False

        put_data["allowedMediaSources"] = [
            {
                "id": str(sources[0].id),
                "name": sources[0].name,
                "released": sources[0].released,
                "deprecated": sources[0].deprecated,
            }
        ]

        put_data["deals"] = [
            {
                "id": str(deal_to_be_added.id),
                "dealId": deal_to_be_added.deal_id,
                "source": deal_to_be_added.source.bidder_slug,
                "name": deal_to_be_added.name,
                "agencyId": str(agency.id),
            },
            {
                "id": None,
                "dealId": "NEW_DEAL",
                "source": sources[0].bidder_slug,
                "name": "NEW DEAL NAME",
                "accountId": str(account.id),
            },
        ]

        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], put_data["name"])
        self.assertEqual(resp_json["data"]["autoAddNewSources"], put_data["autoAddNewSources"])
        self.assertEqual(resp_json["data"]["salesforceUrl"], put_data["salesforceUrl"])

        self.assertEqual(len(resp_json["data"]["allowedMediaSources"]), 1)
        self.assertEqual(resp_json["data"]["allowedMediaSources"][0]["id"], str(sources[0].id))

        self.assertEqual(len(resp_json["data"]["deals"]), 2)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal_to_be_added.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["agencyId"], str(agency.id))
        self.assertEqual(resp_json["data"]["deals"][0]["accountId"], None)
        self.assertEqual(resp_json["data"]["deals"][1]["dealId"], "NEW_DEAL")
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAccounts"], 1)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["agencyId"], None)
        self.assertEqual(resp_json["data"]["deals"][1]["accountId"], str(account.id))

        self.assertIsNone(resp_json["data"]["defaultIconUrl"])

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="icon.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    @mock.patch("utils.slack.publish")
    def test_put_default_icon(self, mock_slack_publish, mock_external_validation, mock_s3_upload, _):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        put_data = resp_json["data"].copy()
        put_data["name"] = "New generic account"

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "icon.url": {
                        "valid": True,
                        "id": "icon_id",
                        "hash": "icon_hash",
                        "width": 150,
                        "height": 150,
                        "file_size": 1000,
                    }
                }
            },
        }
        put_data["default_icon_url"] = None
        put_data[
            "default_icon_base64"
        ] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVR42u3UMQEAAAjDMMC/52EAByQSerSTpICXRgIwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAC4LB6wBfy1zhUaAAAAAElFTkSuQmCC"  # noqa
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])

        account.refresh_from_db()
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(150, account.settings.default_icon.width)
        self.assertEqual(150, account.settings.default_icon.height)
        self.assertEqual(1000, account.settings.default_icon.file_size)
        self.assertIsNone(account.settings.default_icon.origin_url)

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://icon.url.com": {
                        "valid": True,
                        "id": "icon_id2",
                        "hash": "icon_hash2",
                        "width": 130,
                        "height": 130,
                        "file_size": 1001,
                    }
                }
            },
        }
        put_data["default_icon_base64"] = None
        put_data["default_icon_url"] = "http://icon.url.com"
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual("/icon_id2.jpg", resp_json["data"]["defaultIconUrl"])

        account.refresh_from_db()
        self.assertEqual("icon_id2", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash2", account.settings.default_icon.image_hash)
        self.assertEqual(130, account.settings.default_icon.width)
        self.assertEqual(130, account.settings.default_icon.height)
        self.assertEqual(1001, account.settings.default_icon.file_size)
        self.assertEqual("http://icon.url.com", account.settings.default_icon.origin_url)

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "icon.url": {
                        "valid": True,
                        "id": "icon_id3",
                        "hash": "icon_hash3",
                        "width": 190,
                        "height": 190,
                        "file_size": 9000,
                    }
                }
            },
        }
        put_data[
            "default_icon_base64"
        ] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVR42u3UMQEAAAjDMMC/52EAByQSerSTpICXRgIwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAC4LB6wBfy1zhUaAAAAAElFTkSuQmCC"  # noqa
        put_data["default_icon_url"] = "http://icon.url2.com"
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual("/icon_id3.jpg", resp_json["data"]["defaultIconUrl"])

        account.refresh_from_db()
        self.assertEqual("icon_id3", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash3", account.settings.default_icon.image_hash)
        self.assertEqual(190, account.settings.default_icon.width)
        self.assertEqual(190, account.settings.default_icon.height)
        self.assertEqual(9000, account.settings.default_icon.file_size)
        self.assertIsNone(account.settings.default_icon.origin_url)

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="icon.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    @mock.patch("utils.slack.publish")
    def test_put_default_icon_fail(self, mock_slack_publish, mock_external_validation, mock_s3_upload, _):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        put_data = resp_json["data"].copy()
        put_data["name"] = "New generic account"
        put_data["default_icon_base64"] = "data:image/png;base64,123456789012"

        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "icon.url": {
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
        put_data[
            "default_icon_base64"
        ] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVR42u3UMQEAAAjDMMC/52EAByQSerSTpICXRgIwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAC4LB6wBfy1zhUaAAAAAElFTkSuQmCC"  # noqa
        put_data["default_icon_url"] = "http://icon.url.com"
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["valid"] = True
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["id"] = None
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["id"] = "icon_id"
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 151
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 127
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["height"] = 127
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 10001
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["height"] = 10001
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 128
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["height"] = 128
        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])

        account.refresh_from_db()
        self.assertIsNone(account.settings.default_icon.origin_url)

    @mock.patch("utils.slack.publish")
    def test_post(self, mock_slack_publish):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=sources[0])

        new_account = self.account_repr(
            agency_id=agency.id,
            account_name="Generic account",
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user.id,
            auto_add_new_sources=True,
            salesforce_url="http://salesforce.com",
            allowed_media_sources=[],
            deals=[
                {
                    "id": str(deal.id),
                    "dealId": deal.deal_id,
                    "source": deal.source.bidder_slug,
                    "name": deal.name,
                    "agencyId": agency.id,
                },
                {
                    "id": None,
                    "dealId": "NEW_DEAL",
                    "source": sources[0].bidder_slug,
                    "name": "NEW DEAL NAME",
                    "agencyId": agency.id,
                },
            ],
        )

        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["name"], new_account["name"])
        self.assertEqual(resp_json["data"]["agencyId"], str(agency.id))
        self.assertEqual(resp_json["data"]["accountType"], new_account["accountType"])
        self.assertEqual(resp_json["data"]["defaultAccountManager"], new_account["defaultAccountManager"])
        self.assertIsNone(resp_json["data"]["defaultSalesRepresentative"])
        self.assertIsNone(resp_json["data"]["defaultCsRepresentative"])
        self.assertIsNone(resp_json["data"]["obSalesRepresentative"])
        self.assertEqual(resp_json["data"]["autoAddNewSources"], new_account["autoAddNewSources"])
        self.assertEqual(resp_json["data"]["salesforceUrl"], new_account["salesforceUrl"])

        self.assertEqual(len(resp_json["data"]["allowedMediaSources"]), 0)

        self.assertEqual(len(resp_json["data"]["deals"]), 2)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["dealId"], "NEW_DEAL")
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAccounts"], 1)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAdgroups"], 0)

        self.assertIsNone(resp_json["data"]["defaultIconUrl"])

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="icon.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    @mock.patch("utils.slack.publish")
    def test_post_default_icon(self, mock_slack_publish, mock_external_validation, mock_s3_upload, _):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "icon.url": {
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
            agency_id=agency.id,
            account_name="Generic account",
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user.id,
            auto_add_new_sources=True,
            default_icon_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVR42u3UMQEAAAjDMMC/52EAByQSerSTpICXRgIwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAC4LB6wBfy1zhUaAAAAAElFTkSuQmCC",  # noqa
        )
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])

        account = core.models.Account.objects.get(id=resp_json["data"]["id"])
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(170, account.settings.default_icon.width)
        self.assertEqual(170, account.settings.default_icon.height)
        self.assertEqual(2000, account.settings.default_icon.file_size)
        self.assertIsNone(account.settings.default_icon.origin_url)

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://icon.url.com": {
                        "valid": True,
                        "id": "icon_id2",
                        "hash": "icon_hash2",
                        "width": 171,
                        "height": 171,
                        "file_size": 2001,
                    }
                }
            },
        }
        new_account["default_icon_base64"] = None
        new_account["default_icon_url"] = "http://icon.url.com"
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual("/icon_id2.jpg", resp_json["data"]["defaultIconUrl"])

        account = core.models.Account.objects.get(id=resp_json["data"]["id"])
        self.assertEqual("icon_id2", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash2", account.settings.default_icon.image_hash)
        self.assertEqual(171, account.settings.default_icon.width)
        self.assertEqual(171, account.settings.default_icon.height)
        self.assertEqual(2001, account.settings.default_icon.file_size)
        self.assertEqual("http://icon.url.com", account.settings.default_icon.origin_url)

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "icon.url": {
                        "valid": True,
                        "id": "icon_id3",
                        "hash": "icon_hash3",
                        "width": 172,
                        "height": 172,
                        "file_size": 2002,
                    }
                }
            },
        }
        new_account[
            "default_icon_base64"
        ] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVR42u3UMQEAAAjDMMC/52EAByQSerSTpICXRgIwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAC4LB6wBfy1zhUaAAAAAElFTkSuQmCC"  # noqa
        new_account["default_icon_url"] = "http://icon.url2.com"
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual("/icon_id3.jpg", resp_json["data"]["defaultIconUrl"])

        account = core.models.Account.objects.get(id=resp_json["data"]["id"])
        self.assertEqual("icon_id3", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash3", account.settings.default_icon.image_hash)
        self.assertEqual(172, account.settings.default_icon.width)
        self.assertEqual(172, account.settings.default_icon.height)
        self.assertEqual(2002, account.settings.default_icon.file_size)
        self.assertIsNone(account.settings.default_icon.origin_url)

    @mock.patch("django.conf.settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME", return_value="test_mock")
    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="icon.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    @mock.patch("utils.slack.publish")
    def test_post_default_icon_fail(self, mock_slack_publish, mock_external_validation, mock_s3_upload, _):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])

        new_account = self.account_repr(
            agency_id=agency.id,
            account_name="Generic account",
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user.id,
            auto_add_new_sources=True,
            default_icon_base64="invalid_image_base64",
        )
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "icon.url": {
                        "valid": False,
                        "id": "icon_id",
                        "hash": "icon_hash",
                        "width": 150,
                        "height": 150,
                        "file_size": 3000,
                    }
                }
            },
        }
        new_account[
            "default_icon_base64"
        ] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVR42u3UMQEAAAjDMMC/52EAByQSerSTpICXRgIwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMADAAwAAAAwAMAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwAMADAAAADAAwADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAAwAMAAAAMADAC4LB6wBfy1zhUaAAAAAElFTkSuQmCC"  # noqa
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["valid"] = True
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["id"] = None
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["id"] = "icon_id"
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 151
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 127
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["height"] = 127
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 10001
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["height"] = 10001
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        self.assertResponseError(r, "ValidationError")

        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["width"] = 128
        mock_external_validation.return_value["candidate"]["images"]["icon.url"]["height"] = 128
        r = self.client.post(reverse("restapi.account.internal:accounts_list"), data=new_account, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.assertEqual("/icon_id.jpg", resp_json["data"]["defaultIconUrl"])

        account = core.models.Account.objects.get(id=resp_json["data"]["id"])
        self.assertEqual("icon_id", account.settings.default_icon.image_id)
        self.assertEqual("icon_hash", account.settings.default_icon.image_hash)
        self.assertEqual(128, account.settings.default_icon.width)
        self.assertEqual(128, account.settings.default_icon.height)
        self.assertEqual(3000, account.settings.default_icon.file_size)
        self.assertIsNone(account.settings.default_icon.origin_url)

    @mock.patch("restapi.account.internal.helpers.get_non_removable_sources_ids")
    @mock.patch("utils.slack.publish")
    def test_put_allowed_sources_error(self, mock_slack_publish, mock_get_non_removable_sources_ids):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_sales_representative=None,
            ob_account_manager=None,
            auto_add_new_sources=True,
            salesforce_url="http://salesforce.com",
        )

        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list(sources))
        account.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        mock_get_non_removable_sources_ids.return_value = [sources[0].id, sources[1].id]

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["allowedMediaSources"]), 3)
        self.assertEqual(resp_json["data"]["allowedMediaSources"][0]["id"], str(sources[0].id))
        self.assertEqual(resp_json["data"]["allowedMediaSources"][1]["id"], str(sources[1].id))
        self.assertEqual(resp_json["data"]["allowedMediaSources"][2]["id"], str(sources[2].id))

        put_data = resp_json["data"].copy()

        put_data["allowedMediaSources"] = [
            {
                "id": str(sources[2].id),
                "name": sources[2].name,
                "released": sources[2].released,
                "deprecated": sources[2].deprecated,
            }
        ]

        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        r = self.assertResponseError(r, "ValidationError")

        self.assertIn(
            "Can't save changes because media sources {} are still used on this account.".format(
                ", ".join([sources[0].name, sources[1].name])
            ),
            r["details"]["allowedMediaSources"][0],
        )

    def test_put_deals_error(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_sales_representative=None,
            ob_account_manager=None,
            auto_add_new_sources=True,
            salesforce_url="http://salesforce.com",
        )

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal_to_be_added = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        deal_to_be_added_invalid = {"id": str(12345), "dealId": "DEAL_12345", "source": source.bidder_slug}

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        put_data = resp_json["data"].copy()

        put_data["deals"] = [
            {
                "id": str(deal_to_be_added.id),
                "dealId": deal_to_be_added.deal_id,
                "source": deal_to_be_added.source.bidder_slug,
            },
            {
                "id": deal_to_be_added_invalid.get("id"),
                "dealId": deal_to_be_added_invalid.get("dealId"),
                "source": deal_to_be_added_invalid.get("source"),
            },
        ]

        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        r = self.assertResponseError(r, "ValidationError")

        self.assertIn("Deal does not exist", r["details"]["deals"][1]["id"])
