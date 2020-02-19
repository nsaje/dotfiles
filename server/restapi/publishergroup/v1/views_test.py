from django.urls import reverse

import core.features.publisher_groups
from restapi.common.views_base_test import RESTAPITest
from restapi.publishergroup.v1 import views
from utils import test_helper


class PublisherGroupTest(RESTAPITest):
    fixtures = ["test_publishers.yaml"]
    user_id = 2

    def setUp(self):
        super(PublisherGroupTest, self).setUp()
        permissions = [
            "can_edit_publisher_groups",
            "can_use_restapi",
            "can_access_additional_outbrain_publisher_settings",
        ]
        test_helper.add_permissions(self.user, permissions)

        views.PublisherGroupViewSet.throttle_classes = tuple([])

    def publishergroup_repr(self, pg):
        return {"id": str(pg.pk), "name": pg.name, "accountId": str(pg.account_id) if pg.account_id else None}

    def validate_against_db(self, data):
        m = core.features.publisher_groups.PublisherGroup.objects.get(pk=data["id"])
        self.assertDictEqual(data, self.publishergroup_repr(m))

    def test_get_list(self):
        r = self.client.get(reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": 1}))
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.validate_against_db(response["data"][0])
        self.assertEqual(response["data"][0]["id"], "1")

    def test_get_list_now_allowed(self):
        r = self.client.get(reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": 2}))
        self.assertEqual(r.status_code, 404)

    def test_create_new(self):
        r = self.client.post(
            reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": 1}),
            data={"name": "test"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response["data"])

    def test_create_new_not_allowed(self):
        r = self.client.post(
            reverse("restapi.publishergroup.v1:publisher_group_list", kwargs={"account_id": 2}),
            data={"name": "test"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)

    def test_get(self):
        r = self.client.get(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 1, "publisher_group_id": 1}
            )
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])
        self.assertEqual(response["data"]["id"], "1")

    def test_get_now_allowed(self):
        r = self.client.get(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 2, "publisher_group_id": 2}
            )
        )
        self.assertEqual(r.status_code, 404)

    def test_update(self):
        r = self.client.put(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 1, "publisher_group_id": 1}
            ),
            data={"name": "test"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])
        self.assertEqual(response["data"], {"id": "1", "accountId": "1", "name": "test"})

    def test_update_now_allowed(self):
        r = self.client.put(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 2, "publisher_group_id": 2}
            ),
            data={"name": "test"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)

    def test_delete(self):
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 1, "publisher_group_id": 1}
            )
        )
        self.assertEqual(r.status_code, 204)

        # check if really deleted
        r = self.client.get(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 1, "publisher_group_id": 1}
            )
        )
        self.assertEqual(r.status_code, 404)

    def test_delete_now_allowed(self):
        r = self.client.delete(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 2, "publisher_group_id": 2}
            )
        )
        self.assertEqual(r.status_code, 404)

    def test_check_permission(self):
        test_helper.remove_permissions(self.user, ["can_edit_publisher_groups"])
        r = self.client.put(
            reverse(
                "restapi.publishergroup.v1:publisher_group_details", kwargs={"account_id": 1, "publisher_group_id": 1}
            ),
            data={"name": "test"},
            format="json",
        )
        self.assertEqual(r.status_code, 403)
