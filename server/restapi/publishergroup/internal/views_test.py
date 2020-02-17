from django.urls import reverse

import core.features.publisher_groups
from restapi.common.views_base_test import RESTAPITest


class PublisherGroupSearchTest(RESTAPITest):
    fixtures = ["test_publishers.yaml"]

    def publishergroup_repr(self, pg):
        return {
            "id": str(pg.pk),
            "name": pg.name,
            "accountId": str(pg.account_id) if pg.account_id else None,
            "agencyId": str(pg.agency_id) if pg.agency_id else None,
        }

    def test_list(self):
        r = self.client.get(
            reverse("restapi.publishergroup.internal:publisher_group_search", kwargs={"agency_id": 1}) + "?keyword=pg"
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        publisher_groups_db = core.features.publisher_groups.PublisherGroup.objects.filter(id__in=[3, 6, 7])
        self.assertCountEqual(map(self.publishergroup_repr, publisher_groups_db), response["data"])

    def test_list_search_expression(self):
        r = self.client.get(
            reverse("restapi.publishergroup.internal:publisher_group_search", kwargs={"agency_id": 1})
            + "?keyword=agency%20pg%202"
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        publisher_group_db = core.features.publisher_groups.PublisherGroup.objects.get(id=7)
        self.assertCountEqual([self.publishergroup_repr(publisher_group_db)], response["data"])

    def test_list_pagination(self):
        r = self.client.get(
            reverse("restapi.publishergroup.internal:publisher_group_search", kwargs={"agency_id": 1})
            + "?keyword=pg&limit=2"
        )
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        publisher_groups_db = core.features.publisher_groups.PublisherGroup.objects.filter(id__in=[3, 6])
        self.assertCountEqual(map(self.publishergroup_repr, publisher_groups_db), response["data"])

    def test_list_keyword_param_too_long(self):
        r = self.client.get(
            reverse("restapi.publishergroup.internal:publisher_group_search", kwargs={"agency_id": 1})
            + "?keyword="
            + ("1" * 51)
        )
        self.assertEqual(r.status_code, 400)
