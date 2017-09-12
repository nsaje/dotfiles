from django.test import TestCase

import cache_helper


class CacheHelperTest(TestCase):
    def test_get_cache_key(self):
        self.assertEqual(cache_helper.get_cache_key('asd', 'asd'), '85136c79cbf9fe36bb9d05d0639c70c265c18d37')
        self.assertEqual(cache_helper.get_cache_key('asd', 'aad'), '9262531712dfe1c5ea8a37e04ad63c4f40f992ad')

        self.assertEqual(cache_helper.get_cache_key(['asd', 1], 'aad'), '17155bea8f9fd875057f9ff8e7b67c9ee9a5c337')
        self.assertEqual(cache_helper.get_cache_key(['asd', 2], 'aad'), 'c9cdba951c910e037e8191ab7f9ceb04e8dd432e')
