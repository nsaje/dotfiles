import mock
from django.urls import reverse

import core.models
import dash.constants
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AccountViewSetTest(RESTAPITest):
    @classmethod
    def account_repr(
        cls,
        accountId=None,
        agencyId=None,
        accountName=None,
        archived=False,
        currency=dash.constants.Currency.USD,
        frequencyCapping=None,
        accountType=dash.constants.AccountType.UNKNOWN,
        defaultAccountManager=None,
        defaultSalesRepresentative=None,
        defaultCsRepresentative=None,
        obRepresentative=None,
        autoAddNewSources=None,
        salesforceUrl=None,
        mediaSources=[],
    ):
        representation = {
            "id": str(accountId) if accountId is not None else None,
            "agencyId": str(agencyId) if agencyId is not None else None,
            "targeting": {"publisherGroups": {"included": [], "excluded": []}},
            "name": accountName,
            "archived": archived,
            "currency": dash.constants.Currency.get_name(currency),
            "frequencyCapping": frequencyCapping,
            "accountType": dash.constants.AccountType.get_name(accountType),
            "defaultAccountManager": str(defaultAccountManager) if defaultAccountManager is not None else None,
            "defaultSalesRepresentative": str(defaultSalesRepresentative)
            if defaultSalesRepresentative is not None
            else None,
            "defaultCsRepresentative": str(defaultCsRepresentative) if defaultCsRepresentative is not None else None,
            "obRepresentative": str(obRepresentative) if obRepresentative is not None else None,
            "autoAddNewSources": autoAddNewSources,
            "salesforceUrl": salesforceUrl,
            "mediaSources": mediaSources,
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
                    "ob_representative": 3,
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
            "ob_representatives": [{"id": 220, "name": "ob1@outbrain.com"}, {"id": 222, "name": "ob2@outbrain.com"}],
            "hacks": [],
            "deals": [],
        }

        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

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
            resp_json["data"]["obRepresentative"],
            str(agency.ob_representative.id) if agency.ob_representative is not None else None,
        )
        self.assertEqual(resp_json["data"]["autoAddNewSources"], True)
        self.assertEqual(resp_json["data"]["salesforceUrl"], "")

        self.assertEqual(resp_json["data"]["mediaSources"][0]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][1]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][2]["allowed"], True)

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
                        "obRepresentative": "3",
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
                ],
                "hacks": [],
                "deals": [],
            },
        )

    @mock.patch("restapi.account.internal.helpers.get_extra_data")
    def test_get(self, mock_get_extra_data):
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
                    "ob_representative": 3,
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
            "ob_representatives": [{"id": 220, "name": "ob1@outbrain.com"}, {"id": 222, "name": "ob2@outbrain.com"}],
            "hacks": [],
            "deals": [],
        }

        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_representative=None,
            auto_add_new_sources=True,
            salesforce_url="Generic URL",
        )

        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list(sources))
        account.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

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
            resp_json["data"]["obRepresentative"],
            str(account.settings.ob_representative.id) if account.settings.ob_representative is not None else None,
        )
        self.assertEqual(resp_json["data"]["autoAddNewSources"], account.settings.auto_add_new_sources)
        self.assertEqual(resp_json["data"]["salesforceUrl"], account.settings.salesforce_url)
        self.assertEqual(
            resp_json["data"]["mediaSources"],
            [
                {
                    "id": str(sources[0].id),
                    "name": sources[0].name,
                    "released": True,
                    "deprecated": False,
                    "allowed": True,
                },
                {
                    "id": str(sources[1].id),
                    "name": sources[1].name,
                    "released": True,
                    "deprecated": False,
                    "allowed": True,
                },
                {
                    "id": str(sources[2].id),
                    "name": sources[2].name,
                    "released": True,
                    "deprecated": False,
                    "allowed": True,
                },
                {
                    "id": str(sources[3].id),
                    "name": sources[3].name,
                    "released": True,
                    "deprecated": False,
                    "allowed": False,
                },
                {
                    "id": str(sources[4].id),
                    "name": sources[4].name,
                    "released": True,
                    "deprecated": False,
                    "allowed": False,
                },
            ],
        )

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
                        "obRepresentative": "3",
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
                ],
                "hacks": [],
                "deals": [],
            },
        )

    @mock.patch("utils.slack.publish")
    def test_put(self, mock_slack_publish):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_representative=None,
            auto_add_new_sources=True,
            salesforce_url="http://salesforce.com",
        )

        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list(sources))
        account.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["mediaSources"][0]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][1]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][2]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][3]["allowed"], False)
        self.assertEqual(resp_json["data"]["mediaSources"][4]["allowed"], False)

        put_data = resp_json["data"].copy()

        put_data["name"] = "New generic account"
        put_data["salesforceUrl"] = "http://salesforce2.com"
        put_data["autoAddNewSources"] = False

        put_data["mediaSources"][0]["allowed"] = False
        put_data["mediaSources"][3]["allowed"] = True
        put_data["mediaSources"][4]["allowed"] = True

        r = self.client.put(
            reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], put_data["name"])
        self.assertEqual(resp_json["data"]["autoAddNewSources"], put_data["autoAddNewSources"])
        self.assertEqual(resp_json["data"]["salesforceUrl"], put_data["salesforceUrl"])

        self.assertEqual(resp_json["data"]["mediaSources"][0]["allowed"], False)
        self.assertEqual(resp_json["data"]["mediaSources"][1]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][2]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][3]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][4]["allowed"], True)

    @mock.patch("utils.slack.publish")
    def test_post(self, mock_slack_publish):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        new_account = self.account_repr(
            agencyId=agency.id,
            accountName="Generic account",
            accountType=dash.constants.AccountType.ACTIVATED,
            defaultAccountManager=self.user.id,
            autoAddNewSources=True,
            salesforceUrl="http://salesforce.com",
            mediaSources=[],
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
        self.assertIsNone(resp_json["data"]["obRepresentative"])
        self.assertEqual(resp_json["data"]["autoAddNewSources"], new_account["autoAddNewSources"])
        self.assertEqual(resp_json["data"]["salesforceUrl"], new_account["salesforceUrl"])

        self.assertEqual(len(resp_json["data"]["mediaSources"]), 3)
        self.assertEqual(resp_json["data"]["mediaSources"][0]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][1]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][2]["allowed"], True)

    @mock.patch("restapi.account.internal.helpers.get_non_removable_sources_ids")
    @mock.patch("utils.slack.publish")
    def test_put_media_sources_error(self, mock_slack_publish, mock_get_non_removable_sources_ids):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, name="Generic account", users=[self.user])
        account.settings.update_unsafe(
            None,
            name=account.name,
            account_type=dash.constants.AccountType.ACTIVATED,
            default_account_manager=self.user,
            default_sales_representative=None,
            default_cs_representative=None,
            ob_representative=None,
            auto_add_new_sources=True,
            salesforce_url="http://salesforce.com",
        )

        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.allowed_sources.add(*list(sources))
        account.allowed_sources.add(*list([sources[0], sources[1], sources[2]]))

        mock_get_non_removable_sources_ids.return_value = [sources[0].id, sources[1].id]

        r = self.client.get(reverse("restapi.account.internal:accounts_details", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["mediaSources"][0]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][1]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][2]["allowed"], True)
        self.assertEqual(resp_json["data"]["mediaSources"][3]["allowed"], False)
        self.assertEqual(resp_json["data"]["mediaSources"][4]["allowed"], False)

        put_data = resp_json["data"].copy()

        put_data["mediaSources"][0]["allowed"] = False
        put_data["mediaSources"][1]["allowed"] = False

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
            r["details"]["mediaSources"][0],
        )
