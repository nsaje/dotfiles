from django.test import TestCase

import core.features.publisher_groups
from dash import publisher_helpers
from utils.magic_mixer import magic_mixer


class PublisherHelpersTest(TestCase):
    def test_create_publisher_id(self):
        self.assertEqual(publisher_helpers.create_publisher_id("asd", 1), "asd__1")
        self.assertEqual(publisher_helpers.create_publisher_id("asd", None), "asd__")

    def test_dissect_publisher_id(self):
        self.assertEqual(publisher_helpers.dissect_publisher_id("asd__1"), ("asd", 1))
        self.assertEqual(publisher_helpers.dissect_publisher_id("asd__"), ("asd", None))

    def test_inflate_publisher_id_source(self):
        self.assertEqual(
            publisher_helpers.inflate_publisher_id_source("asd__", [1, 2, 3]), ["asd__1", "asd__2", "asd__3"]
        )
        self.assertEqual(publisher_helpers.inflate_publisher_id_source("asd__1", [1, 2, 3]), ["asd__1"])

    def test_is_subdomain_match(self):
        self.assertFalse(publisher_helpers.is_subdomain_match("msn.com", "cnn.com"))
        self.assertFalse(publisher_helpers.is_subdomain_match("msn.com", "www.cnn.com"))
        self.assertFalse(publisher_helpers.is_subdomain_match("msn.com", "money.cnn.com"))
        self.assertFalse(publisher_helpers.is_subdomain_match("msn.com", "http://money.cnn.com"))

        self.assertTrue(publisher_helpers.is_subdomain_match("msn.com", "msn.com"))
        self.assertTrue(publisher_helpers.is_subdomain_match("msn.com", "www.msn.com"))
        self.assertTrue(publisher_helpers.is_subdomain_match("msn.com", "money.msn.com"))
        self.assertTrue(publisher_helpers.is_subdomain_match("msn.com", "http://money.msn.com"))

        self.assertFalse(publisher_helpers.is_subdomain_match("money.msn.com", "msn.com"))
        self.assertFalse(publisher_helpers.is_subdomain_match("money.msn.com", "www.msn.com"))

        self.assertTrue(publisher_helpers.is_subdomain_match("money.msn.com", "money.msn.com"))
        self.assertTrue(publisher_helpers.is_subdomain_match("money.msn.com", "http://money.msn.com"))

    def test_strip_prefix(self):
        self.assertEqual(publisher_helpers.strip_prefix("msn.com"), "msn.com")
        self.assertEqual(publisher_helpers.strip_prefix("http://msn.com"), "msn.com")
        self.assertEqual(publisher_helpers.strip_prefix("https://msn.com"), "msn.com")
        self.assertEqual(publisher_helpers.strip_prefix("http://www.msn.com"), "www.msn.com")

    def test_all_subdomains(self):
        self.assertEqual(publisher_helpers.all_subdomains("www.msn.com"), ["msn.com", "com"])
        self.assertEqual(publisher_helpers.all_subdomains("msn.com"), ["com"])
        self.assertEqual(publisher_helpers.all_subdomains("http://www.msn.com"), ["msn.com", "com"])
        self.assertEqual(publisher_helpers.all_subdomains("https://www.msn.com"), ["msn.com", "com"])


class PublisherIdLookupMapTest(TestCase):
    def test_map_blacklist_over_whitelist(self):
        publisher = "beer.com"
        source_id = 1
        publisher_id = publisher_helpers.create_publisher_id(publisher, source_id)

        black_entry = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher=publisher, source__id=source_id
        )
        white_entry = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher=publisher, source__id=source_id
        )
        blacklist = core.features.publisher_groups.PublisherGroupEntry.objects.filter(pk__in=[black_entry.id])
        whitelist = core.features.publisher_groups.PublisherGroupEntry.objects.filter(pk__in=[white_entry.id])

        m = publisher_helpers.PublisherIdLookupMap(blacklist, whitelist)
        self.assertEqual(m[publisher_id].id, black_entry.id)

    def test_ignore_outbrain_subdomains(self):
        publisher_domain = "pch.com (Outbrain Publisher)"
        publisher_subdomain = "lotto.pch.com (Outbrain Publisher)"
        source_id = 3
        publisher_id_subdomain = publisher_helpers.create_publisher_id(publisher_subdomain, source_id)

        black_entry = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher=publisher_domain, source__id=source_id
        )
        blacklist = core.features.publisher_groups.PublisherGroupEntry.objects.filter(pk__in=[black_entry.id])

        m = publisher_helpers.PublisherIdLookupMap(blacklist)
        self.assertIsNone(m[publisher_id_subdomain])


class PublisherIdVsPlacementLookupMapTest(TestCase):
    def setUp(self):
        self.source = magic_mixer.blend(core.models.Source)
        self.pge_1 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher="example.com", placement=None, source=None
        )
        self.pge_2 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry, publisher="sub.example.com", placement=None, source=None
        )
        self.pge_3 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="example.com",
            placement=None,
            source=self.source,
        )
        self.pge_4 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="sub.example.com",
            placement=None,
            source=self.source,
        )
        self.pge_5 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="example.com",
            placement="someplacement",
            source=None,
        )
        self.pge_6 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="sub.example.com",
            placement="someplacement",
            source=None,
        )
        self.pge_7 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="example.com",
            placement="someplacement",
            source=self.source,
        )
        self.pge_8 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="sub.example.com",
            placement="someplacement",
            source=self.source,
        )
        self.pge_9 = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher="sub.example.com",
            placement="someplacement__with_double_underscore",
            source=self.source,
        )

    def test_filter_publisher(self):
        blacklist = core.features.publisher_groups.PublisherGroupEntry.objects.filter(
            pk__in=[
                self.pge_1.id,
                self.pge_2.id,
                self.pge_3.id,
                self.pge_4.id,
                self.pge_5.id,
                self.pge_6.id,
                self.pge_7.id,
                self.pge_8.id,
                self.pge_9.id,
            ]
        )
        lookup_map = publisher_helpers.PublisherIdLookupMap(blacklist)

        self.assertEquals(lookup_map["example.com__all"], self.pge_1)
        self.assertEquals(lookup_map["sub.example.com__all"], self.pge_2)
        self.assertEquals(lookup_map["example.com__{}".format(self.source.id)], self.pge_3)
        self.assertEquals(lookup_map["sub.example.com__{}".format(self.source.id)], self.pge_4)

        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["example.com__all{}someplacement".format(publisher_helpers.PLACEMENT_SEPARATOR)]
        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["sub.example.com__all{}someplacement".format(publisher_helpers.PLACEMENT_SEPARATOR)]
        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["example.com__{}{}someplacement".format(self.source.id, publisher_helpers.PLACEMENT_SEPARATOR)]
        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map[
                "sub.example.com__{}{}someplacement".format(self.source.id, publisher_helpers.PLACEMENT_SEPARATOR)
            ]

        self.assertEquals(
            {e.id for e in lookup_map._map.values()}, {self.pge_1.id, self.pge_2.id, self.pge_3.id, self.pge_4.id}
        )

    def test_filter_placement(self):
        blacklist = core.features.publisher_groups.PublisherGroupEntry.objects.filter(
            pk__in=[
                self.pge_1.id,
                self.pge_2.id,
                self.pge_3.id,
                self.pge_4.id,
                self.pge_5.id,
                self.pge_6.id,
                self.pge_7.id,
                self.pge_8.id,
                self.pge_9.id,
            ]
        )
        lookup_map = publisher_helpers.PublisherPlacementLookupMap(blacklist)

        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["example.com__all"]
        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["sub.example.com__all"]
        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["example.com__{}".format(self.source.id)]
        with self.assertRaises(publisher_helpers.InvalidLookupKeyFormat):
            lookup_map["sub.example.com__{}".format(self.source.id)]

        self.assertEquals(
            lookup_map["example.com__all{}someplacement".format(publisher_helpers.PLACEMENT_SEPARATOR)], self.pge_5
        )
        self.assertEquals(
            lookup_map["sub.example.com__all{}someplacement".format(publisher_helpers.PLACEMENT_SEPARATOR)], self.pge_6
        )
        self.assertEquals(
            lookup_map["example.com__{}{}someplacement".format(self.source.id, publisher_helpers.PLACEMENT_SEPARATOR)],
            self.pge_7,
        )
        self.assertEquals(
            lookup_map[
                "sub.example.com__{}{}someplacement".format(self.source.id, publisher_helpers.PLACEMENT_SEPARATOR)
            ],
            self.pge_8,
        )
        self.assertEquals(
            lookup_map[
                "sub.example.com__{}{}someplacement__with_double_underscore".format(
                    self.source.id, publisher_helpers.PLACEMENT_SEPARATOR
                )
            ],
            self.pge_9,
        )

        self.assertEquals(
            {e.id for e in lookup_map._map.values()},
            {self.pge_5.id, self.pge_6.id, self.pge_7.id, self.pge_8.id, self.pge_9.id},
        )
