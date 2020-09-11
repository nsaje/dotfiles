import mock
from django.urls import reverse
from rest_framework.test import APIClient

import core.features.publisher_groups
from restapi.common.views_base_test_case import FutureRESTAPITestCase
from restapi.common.views_base_test_case import RESTAPITestCase
from restapi.publishergroupentry.v1 import views
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyPublisherGroupEntryTest(RESTAPITestCase):
    def setUp(self):
        permissions = [
            "can_use_restapi",
            "can_access_additional_outbrain_publisher_settings",
            "can_use_placement_targeting",
        ]

        self.client = APIClient()
        self.user = magic_mixer.blend_user(permissions=permissions)
        self.client.force_authenticate(user=self.user)

        self.source_one = magic_mixer.blend(core.models.Source)
        self.source_two = magic_mixer.blend(core.models.Source)
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=self.agency)
        self.account_no_access = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.publisher_group = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=self.account)
        self.publisher_group_no_access = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=self.account_no_access
        )

        views.PublisherGroupEntryViewSet.throttle_classes = tuple([])

    def publishergroupentry_repr(self, pg, check_outbrain_pub_id):
        d = {
            "id": str(pg.pk),
            "source": pg.source.bidder_slug if pg.source else None,
            "publisher": pg.publisher,
            "includeSubdomains": pg.include_subdomains,
            "placement": pg.placement,
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
        magic_mixer.cycle(5).blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={"offset": 0, "limit": 10},
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.assertEqual(len(response["data"]), 5)
        for item in response["data"]:
            self.validate_against_db(item)

    def test_get_list_check_pagination(self):
        magic_mixer.cycle(2).blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={"offset": 1, "limit": 10},
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        for item in response["data"]:
            self.validate_against_db(item)
        self.assertEqual(len(response["data"]), 1)
        self.assertDictEqual(
            response,
            {
                "count": 2,
                "next": None,
                "previous": "http://testserver/rest/v1/publishergroups/{}/entries/?limit=10".format(
                    self.publisher_group.id
                ),
                "data": mock.ANY,
            },
        )

    def test_get_list_no_access(self):
        magic_mixer.cycle(2).blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group_no_access
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group_no_access.id},
            ),
            data={"offset": 0, "limit": 10},
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_create_new(self):
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={"publisher": "test", "source": self.source_one.bidder_slug, "includeSubdomains": False},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response["data"])
        self.assertIsNone(response["data"]["placement"])

    def test_create_new_placement(self):
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={
                "publisher": "test",
                "source": self.source_one.bidder_slug,
                "includeSubdomains": False,
                "placement": "best_plac",
            },
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response["data"])
        self.assertEqual("best_plac", response["data"]["placement"])

    def test_create_new_no_access(self):
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group_no_access.id},
            ),
            data={"publisher": "test", "source": self.source_one.bidder_slug},
            format="json",
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_create_new_no_placement_permission(self):
        test_helper.remove_permissions(self.user, ["can_use_placement_targeting"])
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={
                "publisher": "test",
                "source": self.source_one.bidder_slug,
                "includeSubdomains": False,
                "placement": "best_plac",
            },
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.assertNotIn("placement", response["data"])
        response["data"]["placement"] = None
        self.validate_against_db(response["data"])

    def test_create_new_empty_placement(self):
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={
                "publisher": "test",
                "source": self.source_one.bidder_slug,
                "includeSubdomains": False,
                "placement": "",
            },
            format="json",
        )
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"placement": ["This field may not be blank."]})

    def test_create_new_not_reported_placement(self):
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data={
                "publisher": "test",
                "source": self.source_one.bidder_slug,
                "includeSubdomains": False,
                "placement": "Not reported",
            },
            format="json",
        )
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"], {"placement": ['Invalid placement: "Not reported"']})

    def test_bulk_create_new(self):
        r = self.client.post(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_list",
                kwargs={"publisher_group_id": self.publisher_group.id},
            ),
            data=[{"publisher": "test"}, {"publisher": "bla"}],
            format="json",
        )
        response = self.assertResponseValid(r, data_type=list, status_code=201)
        for item in response["data"]:
            self.validate_against_db(item)
        self.assertEqual(len(response["data"]), 2)

    def test_get(self):
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            )
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])

    def test_get_not_access(self):
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group_no_access
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group_no_access.id, "entry_id": pge.id},
            )
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_get_no_placement_permission(self):
        test_helper.remove_permissions(self.user, ["can_use_placement_targeting"])
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            )
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.assertNotIn("placement", response["data"])
        response["data"]["placement"] = core.features.publisher_groups.PublisherGroupEntry.objects.get(
            pk=response["data"]["id"]
        ).placement
        self.validate_against_db(response["data"])

    def test_update(self):
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group
        )
        r = self.client.put(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            ),
            data={
                "publisher": "cnn",
                "source": self.source_two.bidder_slug,
                "outbrainPublisherId": "123",
                "placement": "new_plac",
            },
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"])
        self.assertEqual("new_plac", response["data"]["placement"])

    def test_update_no_access(self):
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group_no_access
        )
        r = self.client.put(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group_no_access.id, "entry_id": pge.id},
            ),
            data={"publisher": "cnn", "source": self.source_two.bidder_slug, "outbrainPublisherId": "123"},
            format="json",
        )
        self.assertEqual(r.status_code, 404)
        self.assertResponseError(r, "MissingDataError")

    def test_update_no_placement_permission(self):
        test_helper.remove_permissions(self.user, ["can_use_placement_targeting"])
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group, placement="test"
        )
        old_placement = pge.placement
        new_placement = old_placement + "_new"

        r = self.client.put(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            ),
            data={
                "publisher": "cnn",
                "source": self.source_two.bidder_slug,
                "outbrainPublisherId": "123",
                "placement": new_placement,
            },
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.assertNotIn("placement", response["data"])
        response["data"]["placement"] = old_placement
        self.validate_against_db(response["data"])

    def test_delete(self):
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group
        )
        r = self.client.delete(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            )
        )
        self.assertEqual(r.status_code, 204)

        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            )
        )
        self.assertEqual(r.status_code, 404)

    def test_delete_not_access(self):
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher_group=self.publisher_group_no_access
        )
        r = self.client.delete(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group_no_access.id, "entry_id": pge.id},
            )
        )
        self.assertEqual(r.status_code, 404)

    def test_no_outbrain_permission(self):
        test_helper.remove_permissions(self.user, ["can_access_additional_outbrain_publisher_settings"])
        pge = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher_group=self.publisher_group,
            outbrain_publisher_id="",
        )
        r = self.client.get(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            )
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"], check_outbrain_pub_id=False)

        r = self.client.put(
            reverse(
                "restapi.publishergroupentry.v1:publisher_group_entry_details",
                kwargs={"publisher_group_id": self.publisher_group.id, "entry_id": pge.id},
            ),
            data={"publisher": "cnn", "source": self.source_two.bidder_slug, "outbrainPublisherId": "123"},
            format="json",
        )
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response["data"], check_outbrain_pub_id=False)

        # validate outbrainPublisherId was not changed
        pge.refresh_from_db()
        self.assertEqual(pge.outbrain_publisher_id, "")


class PublisherGroupEntryTest(FutureRESTAPITestCase, LegacyPublisherGroupEntryTest):
    pass
