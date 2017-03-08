from django.test import TestCase

from dash import publisher_helpers


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
