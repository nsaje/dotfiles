from django.test import TestCase

from utils.magic_mixer import magic_mixer

from dash import publisher_helpers

import core.publisher_groups


class PublisherHelpersTest(TestCase):

    def test_create_publisher_id(self):
        self.assertEqual(publisher_helpers.create_publisher_id('asd', 1), 'asd__1')
        self.assertEqual(publisher_helpers.create_publisher_id('asd', None), 'asd__')

    def test_dissect_publisher_id(self):
        self.assertEqual(publisher_helpers.dissect_publisher_id('asd__1'), ('asd', 1))
        self.assertEqual(publisher_helpers.dissect_publisher_id('asd__'), ('asd', None))

    def test_inflate_publisher_id_source(self):
        self.assertEqual(publisher_helpers.inflate_publisher_id_source('asd__', [1, 2, 3]),
                         ['asd__1', 'asd__2', 'asd__3'])
        self.assertEqual(publisher_helpers.inflate_publisher_id_source('asd__1', [1, 2, 3]),
                         ['asd__1'])

    def test_is_subdomain_match(self):
        self.assertFalse(publisher_helpers.is_subdomain_match('msn.com', 'cnn.com'))
        self.assertFalse(publisher_helpers.is_subdomain_match('msn.com', 'www.cnn.com'))
        self.assertFalse(publisher_helpers.is_subdomain_match('msn.com', 'money.cnn.com'))
        self.assertFalse(publisher_helpers.is_subdomain_match('msn.com', 'http://money.cnn.com'))

        self.assertTrue(publisher_helpers.is_subdomain_match('msn.com', 'msn.com'))
        self.assertTrue(publisher_helpers.is_subdomain_match('msn.com', 'www.msn.com'))
        self.assertTrue(publisher_helpers.is_subdomain_match('msn.com', 'money.msn.com'))
        self.assertTrue(publisher_helpers.is_subdomain_match('msn.com', 'http://money.msn.com'))

        self.assertFalse(publisher_helpers.is_subdomain_match('money.msn.com', 'msn.com'))
        self.assertFalse(publisher_helpers.is_subdomain_match('money.msn.com', 'www.msn.com'))

        self.assertTrue(publisher_helpers.is_subdomain_match('money.msn.com', 'money.msn.com'))
        self.assertTrue(publisher_helpers.is_subdomain_match('money.msn.com', 'http://money.msn.com'))

    def test_strip_prefix(self):
        self.assertEqual(publisher_helpers.strip_prefix('msn.com'), 'msn.com')
        self.assertEqual(publisher_helpers.strip_prefix('http://msn.com'), 'msn.com')
        self.assertEqual(publisher_helpers.strip_prefix('https://msn.com'), 'msn.com')
        self.assertEqual(publisher_helpers.strip_prefix('http://www.msn.com'), 'www.msn.com')

    def test_all_subdomains(self):
        self.assertEqual(publisher_helpers.all_subdomains('www.msn.com'), ['msn.com', 'com'])
        self.assertEqual(publisher_helpers.all_subdomains('msn.com'), ['com'])
        self.assertEqual(publisher_helpers.all_subdomains('http://www.msn.com'), ['msn.com', 'com'])
        self.assertEqual(publisher_helpers.all_subdomains('https://www.msn.com'), ['msn.com', 'com'])


class PublisherIdLookupMapTest(TestCase):
    def test_map_blacklist_over_whitelist(self):
        publisher = "beer.com"
        source_id = 1
        publisher_id = publisher_helpers.create_publisher_id(publisher, source_id)

        black_entry = magic_mixer.blend(
            core.publisher_groups.PublisherGroupEntry, publisher=publisher, source__id=source_id)
        white_entry = magic_mixer.blend(
            core.publisher_groups.PublisherGroupEntry, publisher=publisher, source__id=source_id)
        blacklist = core.publisher_groups.PublisherGroupEntry.objects.filter(pk__in=[black_entry.id])
        whitelist = core.publisher_groups.PublisherGroupEntry.objects.filter(pk__in=[white_entry.id])

        m = publisher_helpers.PublisherIdLookupMap(blacklist, whitelist)
        self.assertEqual(m[publisher_id].id, black_entry.id)
