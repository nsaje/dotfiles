import json

from django.urls import reverse

import core.features.bid_modifiers
from core.features.bid_modifiers.service_test import add_non_publisher_bid_modifiers
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest


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
                    "placement": "plac1",
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
                    "placement": None,
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
                    "placement": "plac6",
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
                    "placement": None,
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
                    "placement": "plac1",
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
                    "placement": None,
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

        add_non_publisher_bid_modifiers(source=self.source)

    def repr(self, obj):
        return {
            "id": obj.id,
            "ad_group_id": obj.ad_group_id,
            "publisher": obj.target,
            "source": obj.source.bidder_slug,
            "modifier": obj.modifier,
        }

    def test_get(self):
        test_objs = magic_mixer.cycle(3).blend(
            core.features.bid_modifiers.BidModifier,
            source=self.source,
            source_slug=self.source.bidder_slug,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
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
            core.features.bid_modifiers.BidModifier,
            source=source1,
            source_slug=source1.bidder_slug,
            modifier=1,
            ad_group=(ag for ag in ad_groups[:3]),
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        # different souce
        magic_mixer.cycle(3).blend(
            core.features.bid_modifiers.BidModifier,
            source=source2,
            source_slug=source2.bidder_slug,
            modifier=2,
            ad_group=(ag for ag in ad_groups[:3]),
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        # different_ags
        magic_mixer.cycle(3).blend(
            core.features.bid_modifiers.BidModifier,
            source=source1,
            source_slug=source1.bidder_slug,
            modifier=3,
            ad_group=(ag for ag in ad_groups[3:]),
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
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
            core.features.bid_modifiers.BidModifier,
            source=self.source,
            source_slug=self.source.bidder_slug,
            modifier=(id for id in range(1, 11)),
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        response = self.client.get(reverse("k1api.publisherbidmodifiers"), {"marker": test_objs[2].id, "limit": 5})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs[3:8]])
