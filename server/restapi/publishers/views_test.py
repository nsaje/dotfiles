import json

from django.core.urlresolvers import reverse

import core.models
from core.features.publisher_groups import publisher_group_helpers
import core.features.publisher_bid_modifiers
import restapi.common.views_base_test
from utils.magic_mixer import magic_mixer, get_request_mock


class PublisherBlacklistTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(PublisherBlacklistTest, self).setUp()
        self.test_request = get_request_mock(self.user)
        self.test_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.user])

    def _get_resp_json(self, ad_group_id):
        r = self.client.get(reverse("publishers_list", kwargs={"ad_group_id": ad_group_id}))
        resp_json = json.loads(r.content)
        return resp_json

    def test_adgroups_publishers_list(self):
        source = core.models.Source.objects.get(bidder_slug="gumgum")
        publisher_group_helpers.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn.com", "source": source, "include_subdomains": True}],
            self.test_ad_group,
        )
        publisher_group_helpers.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn2.com", "source": source, "include_subdomains": True}],
            self.test_ad_group.campaign,
        )
        publisher_group_helpers.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn3.com", "source": source, "include_subdomains": True}],
            self.test_ad_group.campaign.account,
        )

        r = self.client.get(reverse("publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}))

        resp_json = json.loads(r.content)
        self.assertEqual(
            resp_json["data"],
            [
                {"name": "cnn.com", "source": "gumgum", "status": "BLACKLISTED", "level": "ADGROUP"},
                {"name": "cnn2.com", "source": "gumgum", "status": "BLACKLISTED", "level": "CAMPAIGN"},
                {"name": "cnn3.com", "source": "gumgum", "status": "BLACKLISTED", "level": "ACCOUNT"},
            ],
        )

    def test_adgroups_publishers_put(self):
        test_blacklist = [
            {"name": "cnn2.com", "source": "gumgum", "status": "BLACKLISTED", "level": "ADGROUP"},
            {"name": "cnn3.com", "source": "gumgum", "status": "BLACKLISTED", "level": "CAMPAIGN"},
            {"name": "cnn4.com", "source": "gumgum", "status": "BLACKLISTED", "level": "ACCOUNT"},
        ]
        r = self.client.put(
            reverse("publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_blacklist,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], test_blacklist)

        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], test_blacklist)

    def test_adgroups_publishers_put_unlist(self):
        source = core.models.Source.objects.get(bidder_slug="gumgum")
        publisher_group_helpers.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn.com", "source": source, "include_subdomains": True}],
            self.test_ad_group,
        )
        publisher_group_helpers.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn2.com", "source": source, "include_subdomains": True}],
            self.test_ad_group.campaign,
        )
        publisher_group_helpers.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn3.com", "source": source, "include_subdomains": True}],
            self.test_ad_group.campaign.account,
        )

        put_data = [
            {"name": "cnn.com", "source": "gumgum", "status": "ENABLED", "level": "ADGROUP"},
            {"name": "cnn2.com", "source": "gumgum", "status": "ENABLED", "level": "CAMPAIGN"},
            {"name": "cnn3.com", "source": "gumgum", "status": "ENABLED", "level": "ACCOUNT"},
        ]
        r = self.client.put(
            reverse("publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}), data=put_data, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], put_data)

        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], [])

    def test_modifiers_get(self):
        source = core.models.Source.objects.get(bidder_slug="gumgum")
        core.features.publisher_bid_modifiers.set(self.test_ad_group, "testpub1", source, 0.5)
        core.features.publisher_bid_modifiers.set(self.test_ad_group, "testpub2", source, 4.6)

        self.assertEqual(
            self._get_resp_json(self.test_ad_group.id)["data"],
            [
                {"level": "ADGROUP", "name": "testpub1", "source": "gumgum", "status": "ENABLED", "modifier": 0.5},
                {"level": "ADGROUP", "name": "testpub2", "source": "gumgum", "status": "ENABLED", "modifier": 4.6},
            ],
        )

    def test_modifiers_set(self):
        source = core.models.Source.objects.get(bidder_slug="gumgum")
        test_put = [
            {"level": "ADGROUP", "name": "testpub1", "source": "gumgum", "status": "ENABLED", "modifier": 0.5},
            {"level": "ADGROUP", "name": "testpub2", "source": "gumgum", "status": "ENABLED", "modifier": 4.6},
        ]
        r = self.client.put(
            reverse("publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}), data=test_put, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], test_put)

        self.assertEqual(
            core.features.publisher_bid_modifiers.get(self.test_ad_group),
            [
                {"publisher": "testpub1", "source": source, "modifier": 0.5},
                {"publisher": "testpub2", "source": source, "modifier": 4.6},
            ],
        )

    def test_modifiers_unset(self):
        source = core.models.Source.objects.get(bidder_slug="gumgum")
        core.features.publisher_bid_modifiers.set(self.test_ad_group, "testpub1", source, 0.5)
        core.features.publisher_bid_modifiers.set(self.test_ad_group, "testpub2", source, 4.6)
        test_put = [{"level": "ADGROUP", "name": "testpub1", "source": "gumgum", "status": "ENABLED", "modifier": None}]
        r = self.client.put(
            reverse("publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}), data=test_put, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], test_put)

        self.assertEqual(
            core.features.publisher_bid_modifiers.get(self.test_ad_group),
            [{"publisher": "testpub2", "source": source, "modifier": 4.6}],
        )
