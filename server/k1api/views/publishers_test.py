import json

from django.core.urlresolvers import reverse

import core.features.publisher_bid_modifiers

import logging

from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PublishersTest(K1APIBaseTest):
    def test_get_publisher_groups(self):
        account_id = 1

        response = self.client.get(reverse("k1api.publisher_groups"), {"account_id": account_id})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data, [{"id": 1, "account_id": 1}, {"id": 11, "account_id": 1}, {"id": 12, "account_id": 1}])

    def test_get_publisher_groups_entries(self):
        account_id = 1

        response = self.client.get(
            reverse("k1api.publisher_groups_entries"), {"account_id": account_id, "offset": 0, "limit": 2}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(
            data,
            [
                {
                    "outbrain_section_id": "",
                    "outbrain_amplify_publisher_id": "",
                    "outbrain_engage_publisher_id": "",
                    "outbrain_publisher_id": "",
                    "publisher": "pub1",
                    "include_subdomains": True,
                    "publisher_group_id": 1,
                    "source_slug": "adblade",
                    "account_id": 1,
                },
                {
                    "outbrain_section_id": "asd1234",
                    "outbrain_amplify_publisher_id": "asd12345",
                    "outbrain_engage_publisher_id": "df164",
                    "outbrain_publisher_id": "asd123",
                    "publisher": "pub2",
                    "include_subdomains": True,
                    "publisher_group_id": 1,
                    "source_slug": None,
                    "account_id": 1,
                },
            ],
        )

    def test_get_publisher_groups_entries_publisher_group_filter(self):
        account_id = 1

        response = self.client.get(
            reverse("k1api.publisher_groups_entries"),
            {"account_id": account_id, "publisher_group_ids": "11,12", "offset": 0, "limit": 2},
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(
            data,
            [
                {
                    "outbrain_section_id": "",
                    "outbrain_amplify_publisher_id": "",
                    "outbrain_engage_publisher_id": "",
                    "outbrain_publisher_id": "",
                    "publisher": "pub6",
                    "include_subdomains": True,
                    "publisher_group_id": 11,
                    "source_slug": "outbrain",
                    "account_id": 1,
                },
                {
                    "outbrain_section_id": "",
                    "outbrain_amplify_publisher_id": "",
                    "outbrain_engage_publisher_id": "",
                    "outbrain_publisher_id": "",
                    "publisher": "pub7",
                    "include_subdomains": True,
                    "publisher_group_id": 12,
                    "source_slug": "outbrain",
                    "account_id": 1,
                },
            ],
        )

    def test_get_publisher_groups_entries_source_slug(self):
        account_id = 1
        source_slug = "adblade"

        response = self.client.get(
            reverse("k1api.publisher_groups_entries"),
            {"account_id": account_id, "source_slug": source_slug, "offset": 0, "limit": 2},
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(
            data,
            [
                {
                    "outbrain_section_id": "",
                    "outbrain_amplify_publisher_id": "",
                    "outbrain_engage_publisher_id": "",
                    "outbrain_publisher_id": "",
                    "publisher": "pub1",
                    "include_subdomains": True,
                    "publisher_group_id": 1,
                    "source_slug": "adblade",
                    "account_id": 1,
                }
            ],
        )

    def test_get_publisher_groups_entries_limit(self):
        account_id = 1

        response = self.client.get(
            reverse("k1api.publisher_groups_entries"), {"account_id": account_id, "offset": 1, "limit": 1}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(
            data,
            [
                {
                    "outbrain_section_id": "asd1234",
                    "outbrain_amplify_publisher_id": "asd12345",
                    "outbrain_engage_publisher_id": "df164",
                    "outbrain_publisher_id": "asd123",
                    "publisher": "pub2",
                    "include_subdomains": True,
                    "publisher_group_id": 1,
                    "source_slug": None,
                    "account_id": 1,
                }
            ],
        )

    def test_get_publisher_groups_entries_no_limit_error(self):
        account_id = 1

        response = self.client.get(reverse("k1api.publisher_groups_entries"), {"account_id": account_id})

        self.assertEqual(response.status_code, 400)


class PublisherBidModifiersTest(K1APIBaseTest):
    def setUp(self):
        self.source = magic_mixer.blend(core.models.Source, bidder_slug="test_source")
        super(PublisherBidModifiersTest, self).setUp()

    def repr(self, obj):
        return {
            "id": obj.id,
            "ad_group_id": obj.ad_group_id,
            "publisher": obj.publisher,
            "source": obj.source.bidder_slug,
            "modifier": obj.modifier,
        }

    def test_get(self):
        test_objs = magic_mixer.cycle(3).blend(
            core.features.publisher_bid_modifiers.PublisherBidModifier, source=self.source
        )
        response = self.client.get(reverse("k1api.publisherbidmodifiers"))
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs])

    def test_get_with_filters(self):
        source1 = magic_mixer.blend(core.models.Source, source_type__type="abc")
        source2 = magic_mixer.blend(core.models.Source, source_type__type="cde")
        ad_groups = magic_mixer.cycle(6).blend(core.models.AdGroup)
        expected = magic_mixer.cycle(3).blend(
            core.features.publisher_bid_modifiers.PublisherBidModifier,
            source=source1,
            modifier=1,
            ad_group=(ag for ag in ad_groups[:3]),
        )
        # different souce
        magic_mixer.cycle(3).blend(
            core.features.publisher_bid_modifiers.PublisherBidModifier,
            source=source2,
            modifier=2,
            ad_group=(ag for ag in ad_groups[:3]),
        )
        # different_ags
        magic_mixer.cycle(3).blend(
            core.features.publisher_bid_modifiers.PublisherBidModifier,
            source=source1,
            modifier=3,
            ad_group=(ag for ag in ad_groups[3:]),
        )
        response = self.client.get(
            reverse("k1api.publisherbidmodifiers"),
            {"ad_group_ids": ",".join(str(ag.id) for ag in ad_groups[:3]), "source_type": "abc"},
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in expected])

    def test_pagination(self):
        test_objs = magic_mixer.cycle(10).blend(
            core.features.publisher_bid_modifiers.PublisherBidModifier,
            source=self.source,
            modifier=(id for id in range(1, 11)),
        )
        response = self.client.get(reverse("k1api.publisherbidmodifiers"), {"marker": test_objs[2].id, "limit": 5})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs[3:8]])
