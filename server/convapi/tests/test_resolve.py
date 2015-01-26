from django.test import TestCase

import convapi.resolve
import dash.models


class ResolveTest(TestCase):
    def test_resolve_source(self):
        s = dash.models.Source(source_type=None, name='Test source', tracking_slug='test', maintenance=False)
        s.save()

        self.assertIsNone(convapi.resolve.resolve_source('test1'))
        self.assertEqual(convapi.resolve.resolve_source('test'), s)
