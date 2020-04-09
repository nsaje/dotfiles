from django.db.models import Q
from django.urls import reverse

import core.features.publisher_groups
import core.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class PublisherGroupTest(RESTAPITest):
    def test_list_with_agency(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account2 = magic_mixer.blend(core.models.Account, users=[self.user])

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
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account2 = magic_mixer.blend(core.models.account.Account, users=[self.user])

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
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

        magic_mixer.cycle(3).blend(core.features.publisher_groups.PublisherGroup, agency=agency)
        magic_mixer.cycle(4).blend(core.features.publisher_groups.PublisherGroup, account=account)

        r = self.client.get(reverse("restapi.publishergroup.internal:publishergroup_list"))
        resp_json = self.assertResponseError(r, "ValidationError")
        error_message = "Either agency id or account id must be provided."
        self.assertIn(error_message, resp_json["details"])

    def test_list_with_keyword(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account2 = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

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

    def test_list_pagination(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
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
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
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
