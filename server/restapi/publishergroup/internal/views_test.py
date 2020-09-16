import rest_framework.status
from django.db.models import Q
from django.urls import reverse
from rest_framework.test import APIClient

import core.features.history
import core.features.publisher_groups
import core.models
import dash.constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models import User


class PublisherGroupTest(RESTAPITestCase):
    def test_list(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)

        publisher_group_1 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=agency, default_include_subdomains=True
        )
        publisher_group_2 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=account, default_include_subdomains=False
        )

        r = self.client.get(reverse("restapi.publishergroup.internal:publishergroup_list"), {"agencyId": agency.id})
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)

        self.assertEqual(
            response["data"],
            [
                {
                    "id": str(publisher_group_1.id),
                    "name": publisher_group_1.name,
                    "accountId": None,
                    "includeSubdomains": True,
                    "agencyId": str(agency.id),
                    "agencyName": publisher_group_1.agency.name,
                    "createdDt": publisher_group_1.created_dt.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "implicit": publisher_group_1.implicit,
                    "level": None,
                    "levelId": None,
                    "levelName": "",
                    "modifiedDt": publisher_group_1.modified_dt.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "size": 0,
                    "type": None,
                },
                {
                    "id": str(publisher_group_2.id),
                    "name": publisher_group_2.name,
                    "accountId": str(account.id),
                    "includeSubdomains": False,
                    "agencyId": None,
                    "accountName": publisher_group_2.account.settings.name,
                    "createdDt": publisher_group_2.created_dt.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "implicit": publisher_group_2.implicit,
                    "level": None,
                    "levelId": None,
                    "levelName": "",
                    "modifiedDt": publisher_group_2.modified_dt.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "size": 0,
                    "type": None,
                },
            ],
        )

    def test_list_with_agency(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = self.mix_account(self.user, permissions=[Permission.READ])

        publisher_groups_1 = magic_mixer.cycle(3).blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        publisher_groups_2 = magic_mixer.cycle(4).blend(core.features.publisher_groups.PublisherGroup, account=account)
        magic_mixer.cycle(5).blend(core.features.publisher_groups.PublisherGroup, account=account2)

        r = self.client.get(reverse("restapi.publishergroup.internal:publishergroup_list"), {"agencyId": agency.id})
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.assertEqual(len(response["data"]), 7)

        response_ids = [int(item.get("id")) for item in response["data"]]
        expected_response_ids = [item.id for item in publisher_groups_1] + [item.id for item in publisher_groups_2]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_with_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = self.mix_account(self.user, permissions=[Permission.READ])

        publisher_groups_1 = magic_mixer.cycle(3).blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        publisher_groups_2 = magic_mixer.cycle(4).blend(core.features.publisher_groups.PublisherGroup, account=account)
        magic_mixer.cycle(5).blend(core.features.publisher_groups.PublisherGroup, account=account2)

        r = self.client.get(reverse("restapi.publishergroup.internal:publishergroup_list"), {"accountId": account.id})
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.assertEqual(len(response["data"]), 7)

        response_ids = [int(item.get("id")) for item in response["data"]]
        expected_response_ids = [item.id for item in publisher_groups_1] + [item.id for item in publisher_groups_2]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_without_agency_and_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)

        magic_mixer.cycle(3).blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        magic_mixer.cycle(4).blend(core.features.publisher_groups.PublisherGroup, account=account)

        r = self.client.get(reverse("restapi.publishergroup.internal:publishergroup_list"))
        resp_json = self.assertResponseError(r, "ValidationError")
        error_message = "Either agency id or account id must be provided."
        self.assertIn(error_message, resp_json["details"])

    def test_list_with_keyword(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = magic_mixer.blend(core.models.Account, agency=agency)

        publisher_groups_1 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=agency, name="test keyword 2"
        )
        publisher_groups_2 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=account, name="test keyword"
        )
        magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account2, name="test")

        r = self.client.get(
            reverse("restapi.publishergroup.internal:publishergroup_list"),
            {"agencyId": agency.id, "keyword": "keyword"},
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.assertEqual(len(response["data"]), 2)

        response_ids = [int(item.get("id")) for item in response["data"]]
        expected_response_ids = [publisher_groups_1.id, publisher_groups_2.id]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_list_without_implicit_publisher_groups(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=agency, name="implicit publisher group", implicit=True
        )

        r = self.client.get(
            reverse("restapi.publishergroup.internal:publishergroup_list"), {"agencyId": agency.id, "implicit": False}
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.assertEqual(len(response["data"]), 0)

    def test_list_pagination(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        publisher_groups = magic_mixer.cycle(20).blend(core.features.publisher_groups.PublisherGroup, agency=agency)

        r = self.client.get(
            reverse("restapi.publishergroup.internal:publishergroup_list"),
            {"agencyId": agency.id, "offset": "0", "limit": "20"},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        response_ids = [int(item.get("id")) for item in resp_json["data"]]
        expected_response_ids = [item.id for item in publisher_groups]
        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

        r_paginated = self.client.get(
            reverse("restapi.publishergroup.internal:publishergroup_list"),
            {"agencyId": agency.id, "offset": 10, "limit": 10},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)

        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        self.assertEqual(resp_json["data"][10:20], resp_json_paginated["data"])

        response_ids = [int(item.get("id")) for item in resp_json_paginated["data"]]
        expected_response_qs = (
            core.features.publisher_groups.PublisherGroup.objects.filter(Q(agency=agency) | Q(account__agency=agency))
            .order_by("-created_dt", "name")
            .only("id")
        )
        expected_response_ids = [item.id for item in expected_response_qs][10:20]

        self.assertEqual(sorted(response_ids), sorted(expected_response_ids))

    def test_remove(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=agency, account=None, name="Publisher group test"
        )

        self.assertEqual(core.features.publisher_groups.PublisherGroup.objects.filter(id=publisher_group.id).count(), 1)

        r = self.client.delete(
            reverse(
                "restapi.publishergroup.internal:publishergroup_details",
                kwargs={"publisher_group_id": publisher_group.id},
            )
        )
        self.assertEqual(r.status_code, 204)

        self.assertEqual(core.features.publisher_groups.PublisherGroup.objects.filter(id=publisher_group.id).count(), 0)

        r = self.client.delete(
            reverse(
                "restapi.publishergroup.internal:publishergroup_details",
                kwargs={"publisher_group_id": publisher_group.id},
            )
        )
        self.assertEqual(r.status_code, 404)


class AddToPublisherGroupTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        self.source = magic_mixer.blend(core.models.Source)
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.other_account = magic_mixer.blend(core.models.Account)
        self.publisher_1 = "example.com"
        self.publisher_2 = "publisher.com"
        self.placement_2 = "00000000-0029-e16a-0000-000000000071"
        self.pg_1 = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        self.pg_2_name = "new publisher group"
        self.pg_other = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.other_account)

    def test_add_to_existing_publisher_group(self):
        request_data = {
            "id": str(self.pg_1.id),
            "name": self.pg_1.name,
            "accountId": str(self.pg_1.account.id),
            "agencyId": None,
            "defaultIncludeSubdomains": self.pg_1.default_include_subdomains,
            "entries": [
                {"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True},
                {
                    "source": self.source.bidder_slug,
                    "publisher": self.publisher_2,
                    "placement": self.placement_2,
                    "includeSubdomains": False,
                },
            ],
        }

        self.assertEqual(self.pg_1.entries.count(), 0)

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_202_ACCEPTED)

        self.assertEqual(self.pg_1.entries.count(), 2)
        pge_1 = self.pg_1.entries.first()
        pge_2 = self.pg_1.entries.last()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": str(self.pg_1.id),
                    "name": self.pg_1.name,
                    "accountId": str(self.pg_1.account.id),
                    "agencyId": None,
                    "defaultIncludeSubdomains": self.pg_1.default_include_subdomains,
                    "entries": [
                        {
                            "id": str(pge_1.id),
                            "source": pge_1.source.bidder_slug,
                            "publisher": self.publisher_1,
                            "placement": None,
                            "publisherGroupId": str(self.pg_1.id),
                            "includeSubdomains": True,
                        },
                        {
                            "id": str(pge_2.id),
                            "source": pge_2.source.bidder_slug,
                            "publisher": self.publisher_2,
                            "placement": self.placement_2,
                            "publisherGroupId": str(self.pg_1.id),
                            "includeSubdomains": False,
                        },
                    ],
                }
            },
        )

    def test_create_publisher_group_and_add(self):
        request_data = {
            "id": None,
            "name": self.pg_2_name,
            "accountId": None,
            "agencyId": str(self.agency.id),
            "defaultIncludeSubdomains": False,
            "entries": [
                {"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True},
                {
                    "source": self.source.bidder_slug,
                    "publisher": self.publisher_2,
                    "placement": self.placement_2,
                    "includeSubdomains": False,
                },
            ],
        }

        self.assertFalse(core.features.publisher_groups.PublisherGroup.objects.filter(name=self.pg_2_name).exists())

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_202_ACCEPTED)

        self.assertEqual(core.features.publisher_groups.PublisherGroup.objects.filter(name=self.pg_2_name).count(), 1)
        pg_2 = core.features.publisher_groups.PublisherGroup.objects.get(name=self.pg_2_name)
        self.assertFalse(pg_2.implicit)
        self.assertEqual(pg_2.entries.count(), 2)
        pge_1 = pg_2.entries.first()
        pge_2 = pg_2.entries.last()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": str(pg_2.id),
                    "name": self.pg_2_name,
                    "accountId": None,
                    "agencyId": str(self.agency.id),
                    "defaultIncludeSubdomains": False,
                    "entries": [
                        {
                            "id": str(pge_1.id),
                            "source": pge_1.source.bidder_slug,
                            "publisher": self.publisher_1,
                            "placement": None,
                            "publisherGroupId": str(pg_2.id),
                            "includeSubdomains": True,
                        },
                        {
                            "id": str(pge_2.id),
                            "source": pge_2.source.bidder_slug,
                            "publisher": self.publisher_2,
                            "placement": self.placement_2,
                            "publisherGroupId": str(pg_2.id),
                            "includeSubdomains": False,
                        },
                    ],
                }
            },
        )

    def test_add_to_invalid_publisher_group(self):
        request_data = {
            "id": str(self.pg_other.id),
            "name": self.pg_other.name,
            "accountId": str(self.pg_other.account.id),
            "agencyId": None,
            "defaultIncludeSubdomains": self.pg_other.default_include_subdomains,
            "entries": [{"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True}],
        }

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"id": ["PublisherGroup matching query does not exist."]})

    def test_add_to_invalid_account(self):
        request_data = {
            "id": None,
            "name": self.pg_2_name,
            "accountId": str(self.other_account.id),
            "agencyId": None,
            "defaultIncludeSubdomains": True,
            "entries": [{"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True}],
        }

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"accountId": ["Account does not exist"]})

    def test_add_to_both_agency_and_account(self):
        request_data = {
            "id": None,
            "name": self.pg_2_name,
            "accountId": str(self.account.id),
            "agencyId": str(self.agency.id),
            "defaultIncludeSubdomains": True,
            "entries": [{"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True}],
        }

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            response["details"],
            {
                "accountId": ["Only one of either account or agency must be set."],
                "agencyId": ["Only one of either account or agency must be set."],
            },
        )

    def test_missing_required_fields(self):
        request_data = {}

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            response["details"], {"name": ["This field is required."], "entries": ["This field is required."]}
        )

        request_data = {"name": self.pg_2_name, "entries": []}

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )

        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"entries": ["At least one entry is required"]})

        request_data = {
            "name": self.pg_2_name,
            "entries": [{"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True}],
        }

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )

        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            response["details"], {"defaultIncludeSubdomains": ["'None' value must be either True or False."]}
        )

    def test_defaults(self):
        request_data = {
            "name": self.pg_2_name,
            "defaultIncludeSubdomains": True,
            "entries": [{"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True}],
        }

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )

        self.assertEqual(r.status_code, rest_framework.status.HTTP_202_ACCEPTED)

        self.assertEqual(core.features.publisher_groups.PublisherGroup.objects.filter(name=self.pg_2_name).count(), 1)
        pg_2 = core.features.publisher_groups.PublisherGroup.objects.get(name=self.pg_2_name)
        self.assertFalse(pg_2.implicit)
        self.assertEqual(pg_2.entries.count(), 1)
        pge_1 = pg_2.entries.first()
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": str(pg_2.id),
                    "name": self.pg_2_name,
                    "accountId": None,
                    "agencyId": None,
                    "defaultIncludeSubdomains": True,
                    "entries": [
                        {
                            "id": str(pge_1.id),
                            "source": pge_1.source.bidder_slug,
                            "publisher": self.publisher_1,
                            "placement": None,
                            "publisherGroupId": str(pg_2.id),
                            "includeSubdomains": True,
                        }
                    ],
                }
            },
        )

    def test_replace_publisher_group_entries_with_history(self):
        def _get_history_entries():
            return core.features.history.History.objects.filter(
                created_by=self.user,
                level=dash.constants.HistoryLevel.GLOBAL,
                action_type=dash.constants.HistoryActionType.GLOBAL_PUBLISHER_BLACKLIST_CHANGE,
            )

        pge_a = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            source=self.source,
            publisher=self.publisher_2,
            placement=self.placement_2,
            includeSubdomains=False,
            publisher_group=self.pg_1,
        )
        pge_b = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            source=self.source,
            publisher=self.publisher_1,
            includeSubdomains=True,
            publisher_group=self.pg_1,
        )
        pge_c = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            source=self.source,
            publisher=self.publisher_2,
            includeSubdomains=True,
            publisher_group=self.pg_1,
        )

        self.assertEqual(self.pg_1.entries.count(), 3)

        self.assertEqual(_get_history_entries().count(), 0)

        request_data = {
            "id": str(self.pg_1.id),
            "name": self.pg_1.name,
            "accountId": str(self.pg_1.account.id),
            "agencyId": None,
            "defaultIncludeSubdomains": self.pg_1.default_include_subdomains,
            "entries": [
                {"source": self.source.bidder_slug, "publisher": self.publisher_1, "includeSubdomains": True},
                {
                    "source": self.source.bidder_slug,
                    "publisher": self.publisher_2,
                    "placement": self.placement_2,
                    "includeSubdomains": False,
                },
            ],
        }

        r = self.client.post(
            reverse("restapi.publishergroup.internal:publishergroup_add"), data=request_data, format="json"
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_202_ACCEPTED)

        self.assertEqual(self.pg_1.entries.count(), 3)
        pges = list(self.pg_1.entries.order_by("id"))
        pge_1 = pges[-2]
        pge_2 = pges[-1]
        self.assertEqual(
            r.json(),
            {
                "data": {
                    "id": str(self.pg_1.id),
                    "name": self.pg_1.name,
                    "accountId": str(self.pg_1.account.id),
                    "agencyId": None,
                    "defaultIncludeSubdomains": self.pg_1.default_include_subdomains,
                    "entries": [
                        {
                            "id": str(pge_c.id),
                            "source": pge_c.source.bidder_slug,
                            "publisher": self.publisher_2,
                            "placement": None,
                            "publisherGroupId": str(self.pg_1.id),
                            "includeSubdomains": True,
                        },
                        {
                            "id": str(pge_1.id),
                            "source": pge_1.source.bidder_slug,
                            "publisher": self.publisher_1,
                            "placement": None,
                            "publisherGroupId": str(self.pg_1.id),
                            "includeSubdomains": True,
                        },
                        {
                            "id": str(pge_2.id),
                            "source": pge_2.source.bidder_slug,
                            "publisher": self.publisher_2,
                            "placement": self.placement_2,
                            "publisherGroupId": str(self.pg_1.id),
                            "includeSubdomains": False,
                        },
                    ],
                }
            },
        )

        self.assertFalse(
            core.features.publisher_groups.PublisherGroupEntry.objects.filter(id__in=[pge_a.id, pge_b.id]).exists()
        )

        history_entries = list(_get_history_entries())
        self.assertEqual(len(history_entries), 1)
        self.assertTrue("Added the following publishers globally" in history_entries[0].changes_text)


class PublisherGroupConnectionsTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.publisher_group_1 = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        self.publisher_group_2 = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, agency=self.agency)
        self.agency.settings.update(None, whitelist_publisher_groups=[self.publisher_group_2.id])
        self.account.settings.update(None, blacklist_publisher_groups=[self.publisher_group_1.id])
        self.campaign.settings.update(None, whitelist_publisher_groups=[self.publisher_group_1.id])
        self.ad_group.settings.update(None, blacklist_publisher_groups=[self.publisher_group_2.id])

    def test_get_publisher_group_connections(self):
        r = self.client.get(
            reverse(
                "restapi.publishergroup.internal:publishergroup_connections",
                kwargs={"publisher_group_id": self.publisher_group_2.id},
            ),
            format="json",
        )
        response = self.assertResponseValid(r, data_type=list, status_code=rest_framework.status.HTTP_200_OK)
        self.assertCountEqual(
            response["data"],
            [
                {
                    "id": str(self.agency.id),
                    "name": self.agency.name,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AGENCY_WHITELIST,
                },
                {
                    "id": str(self.ad_group.id),
                    "name": self.ad_group.name,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                },
            ],
        )

    def test_get_publisher_group_connections_foreign_entities(self):
        client = APIClient()
        user = magic_mixer.blend(User)
        client.force_authenticate(user=user)
        r = client.get(
            reverse(
                "restapi.publishergroup.internal:publishergroup_connections",
                kwargs={"publisher_group_id": self.publisher_group_2.id},
            ),
            format="json",
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_404_NOT_FOUND)
        response = self.assertResponseError(r, "MissingDataError")
        self.assertEqual(response["details"], "Publisher group does not exist")

    def test_remove_publisher_group_connection(self):
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.internal:remove_publishergroup_connection",
                kwargs={
                    "publisher_group_id": self.publisher_group_2.id,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                    "entity_id": self.ad_group.id,
                },
            ),
            format="json",
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_204_NO_CONTENT)
        self.assertEqual(r.content, b"")

        r = self.client.get(
            reverse(
                "restapi.publishergroup.internal:publishergroup_connections",
                kwargs={"publisher_group_id": self.publisher_group_2.id},
            ),
            format="json",
        )
        response = self.assertResponseValid(r, data_type=list, status_code=rest_framework.status.HTTP_200_OK)
        self.assertCountEqual(
            response["data"],
            [
                {
                    "id": str(self.agency.id),
                    "name": self.agency.name,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AGENCY_WHITELIST,
                }
            ],
        )

    def test_remove_publisher_group_connection_wrong_publisher_group_id(self):
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.internal:remove_publishergroup_connection",
                kwargs={
                    "publisher_group_id": self.publisher_group_1.id,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                    "entity_id": self.ad_group.id,
                },
            ),
            format="json",
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"publisherGroupId": ["Publisher group does not exist"]})

    def test_remove_publisher_group_connection_wrong_entity_id(self):
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.internal:remove_publishergroup_connection",
                kwargs={
                    "publisher_group_id": self.publisher_group_2.id,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                    "entity_id": self.ad_group.id + 1,
                },
            ),
            format="json",
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"entityId": ["Connection does not exist"]})

    def test_remove_publisher_group_connection_foreign_entities(self):
        client = APIClient()
        user = magic_mixer.blend(User)
        client.force_authenticate(user=user)
        r = client.delete(
            reverse(
                "restapi.publishergroup.internal:remove_publishergroup_connection",
                kwargs={
                    "publisher_group_id": self.publisher_group_2.id,
                    "location": core.features.publisher_groups.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                    "entity_id": self.ad_group.id,
                },
            ),
            format="json",
        )
        self.assertEqual(r.status_code, rest_framework.status.HTTP_400_BAD_REQUEST)
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"publisherGroupId": ["Publisher group does not exist"]})
