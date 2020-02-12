import mock
from django.urls import reverse

import core.features.publisher_groups
from restapi.common.views_base_test import RESTAPITest
from utils import test_helper

from . import views


class PublisherGroupEntryTest(RESTAPITest):
    fixtures = ["test_publishers.yaml"]
    user_id = 2

    def setUp(self):
        super(PublisherGroupEntryTest, self).setUp()
        permissions = [
            "can_edit_publisher_groups",
            "can_use_restapi",
            "can_access_additional_outbrain_publisher_settings",
        ]
        test_helper.add_permissions(self.user, permissions)

        views.PublisherGroupEntryViewSet.throttle_classes = tuple([])

    def publishergroupentry_repr(self, pg, check_outbrain_pub_id):
        d = {
            "id": str(pg.pk),
            "publisher": pg.publisher,
            "source": pg.source.bidder_slug if pg.source else None,
            "includeSubdomains": pg.include_subdomains,
            "publisherGroupId": str(pg.publisher_group_id),
        }

        if check_outbrain_pub_id:
            d["outbrainPublisherId"] = pg.outbrain_publisher_id
            d["outbrainSectionId"] = pg.outbrain_section_id
            d["outbrainAmplifyPublisherId"] = pg.outbrain_amplify_publisher_id
            d["outbrainEngagePublisherId"] = pg.outbrain_engage_publisher_id

        return d

    def validate_against_db(self, data, check_outbrain_pub_id=True):
        m = core.features.publisher_groups.PublisherGroupEntry.objects.get(pk=data["id"])
        self.assertDictEqual(data, self.publishergroupentry_repr(m, check_outbrain_pub_id))

    def test_get_list(self):
        r = self.client.get(
            reverse("publisher_group_entry_list", kwargs={"publisher_group_id": 1}), data={"offset": 0, "limit": 10}
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        for x in response["data"]:
            self.validate_against_db(x)
        self.assertCountEqual([x["id"] for x in response["data"]], ["1", "2"])

    def test_get_list_check_pagination(self):
        r = self.client.get(
            reverse("publisher_group_entry_list", kwargs={"publisher_group_id": 1}), data={"offset": 1, "limit": 10}
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        for x in response["data"]:
            self.validate_against_db(x)
        self.assertEqual(len(response["data"]), 1)
        self.assertDictEqual(
            response,
            {
                "count": 2,
                "next": None,
                "previous": "http://testserver/rest/v1/publishergroups/1/entries/?limit=10",
                "data": mock.ANY,
            },
        )

    def test_get_list_not_allowed(self):
        r = self.client.get(reverse("publisher_group_entry_list", kwargs={"publisher_group_id": 2}), data={"page": 1})
        self.assertEqual(r.status_code, 404)

    def test_create_new(self):
        r = self.client.post(
            reverse("publisher_group_entry_list", kwargs={"publisher_group_id": 1}),
            data={"publisher": "test", "source": "adsnative", "includeSubdomains": False},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response["data"])

    def test_create_new_now_allowed(self):
        r = self.client.post(
            reverse("publisher_group_entry_list", kwargs={"publisher_group_id": 2}),
            data={"publisher": "test", "source": "adsnative"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)

    def test_bulk_create_new(self):
        r = self.client.post(
            reverse("publisher_group_entry_list", kwargs={"publisher_group_id": 1}),
            data=[{"publisher": "test"}, {"publisher": "bla"}],
            format="json",
        )
        response = self.assertResponseValid(r, data_type=list, status_code=201)
        for x in response["data"]:
            self.validate_against_db(x)
        self.assertEqual(len(response["data"]), 2)

    def test_get(self):
        r = self.client.get(reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 1, "entry_id": 1}))
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])

    def test_get_not_allowed(self):
        r = self.client.get(reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 2, "entry_id": 3}))
        self.assertEqual(r.status_code, 404)

    def test_update(self):
        r = self.client.put(
            reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 1, "entry_id": 1}),
            data={"publisher": "cnn", "source": "gravity", "outbrainPublisherId": "123"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])

    def test_update_not_allowed(self):
        r = self.client.put(
            reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 2, "entry_id": 3}),
            data={"publisher": "cnn", "source": "gravity", "outbrainPublisherId": "123"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)

    def test_delete(self):
        r = self.client.delete(
            reverse("publisher_group_entry_details", kwargs={"publisher_group_id": "1", "entry_id": "1"})
        )
        self.assertEqual(r.status_code, 204)

        r = self.client.get(reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 1, "entry_id": 1}))
        self.assertEqual(r.status_code, 404)

    def test_delete_not_allowed(self):
        r = self.client.delete(
            reverse("publisher_group_entry_details", kwargs={"publisher_group_id": "2", "entry_id": "3"})
        )
        self.assertEqual(r.status_code, 404)

    def test_check_permission(self):
        test_helper.remove_permissions(self.user, ["can_edit_publisher_groups"])
        r = self.client.get(reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 1, "entry_id": 1}))
        self.assertEqual(r.status_code, 403)

    def test_no_outbrain_permission(self):
        test_helper.remove_permissions(self.user, ["can_access_additional_outbrain_publisher_settings"])

        r = self.client.get(reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 1, "entry_id": 1}))
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"], check_outbrain_pub_id=False)

        r = self.client.put(
            reverse("publisher_group_entry_details", kwargs={"publisher_group_id": 1, "entry_id": 1}),
            data={"publisher": "cnn", "source": "gravity", "outbrainPublisherId": "123"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"], check_outbrain_pub_id=False)

        # validate outbrainPublisherId was not changed
        self.assertEqual(core.features.publisher_groups.PublisherGroupEntry.objects.get(pk=1).outbrain_publisher_id, "")
