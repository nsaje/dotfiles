from django.urls import reverse
from rest_framework.test import APIClient

import core.features.publisher_groups
import core.models
from restapi.common.views_base_test_case import RESTAPITestCase
from restapi.publishergroup.v1 import views
from utils.magic_mixer import magic_mixer
from utils.test_helper import add_permissions
from zemauth.features.entity_permission import Permission


class PublisherGroupTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        add_permissions(self.user, ["can_access_additional_outbrain_publisher_settings"])

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=self.agency)
        self.account_no_access = magic_mixer.blend(core.models.Account, agency=self.agency)

        views.PublisherGroupViewSet.throttle_classes = tuple([])

    def publishergroup_repr(self, pg):
        return {"id": str(pg.pk), "name": pg.name, "accountId": str(pg.account_id) if pg.account_id else None}

    def validate_against_db(self, data):
        m = core.features.publisher_groups.PublisherGroup.objects.get(pk=data["id"])
        self.assertDictEqual(data, self.publishergroup_repr(m))

    def test_get_list(self):
        magic_mixer.cycle(5).blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        r = self.client.get(
            reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": self.account.id})
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.assertEqual(len(response["data"]), 5)
        for item in response["data"]:
            self.validate_against_db(item)

    def test_get_list_no_access(self):
        magic_mixer.cycle(5).blend(core.features.publisher_groups.PublisherGroup, account=self.account_no_access)
        r = self.client.get(
            reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": self.account_no_access.id})
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_create_new(self):
        r = self.client.post(
            reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": self.account.id}),
            data={"name": "test"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response["data"])

    def test_create_new_no_access(self):
        r = self.client.post(
            reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": self.account_no_access.id}),
            data={"name": "test"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_get(self):
        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        r = self.client.get(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account.id, "publisher_group_id": publisher_group.id},
            )
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])
        self.assertEqual(response["data"]["id"], str(publisher_group.id))

    def test_get_no_access(self):
        publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=self.account_no_access
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account_no_access.id, "publisher_group_id": publisher_group.id},
            )
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_update(self):
        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        r = self.client.put(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account.id, "publisher_group_id": publisher_group.id},
            ),
            data={"name": "test"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])
        self.assertEqual(
            response["data"], {"id": str(publisher_group.id), "accountId": str(self.account.id), "name": "test"}
        )

    def test_update_no_access(self):
        publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=self.account_no_access
        )
        r = self.client.put(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account_no_access.id, "publisher_group_id": publisher_group.id},
            ),
            data={"name": "test"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_delete(self):
        publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account.id, "publisher_group_id": publisher_group.id},
            )
        )
        self.assertEqual(r.status_code, 204)

        # check if really deleted
        r = self.client.get(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account.id, "publisher_group_id": publisher_group.id},
            )
        )
        self.assertEqual(r.status_code, 404)

    def test_delete_no_access(self):
        publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=self.account_no_access
        )
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details",
                kwargs={"account_id": self.account_no_access.id, "publisher_group_id": publisher_group.id},
            )
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")
