from unittest import mock

from django.core.cache import caches

import core.models
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from . import realtimechanges


class TestCase(BaseTestCase):
    @mock.patch("utils.outbrain_internal_helper.to_internal_ids", autospec=True)
    def test_mark_ad_pending(self, mock_to_internal_ids):
        ca = magic_mixer.blend(core.models.ContentAd)
        cas = magic_mixer.blend(core.models.ContentAdSource, content_ad=ca, source_content_ad_id="abc")
        mock_to_internal_ids.side_effect = lambda external_ids: [123] if external_ids == ["abc"] else []

        realtimechanges.mark_ad_pending(cas)

        cache_key = realtimechanges._get_cache_key(123)
        self.assertEqual(caches[realtimechanges.CACHE_NAME].get(cache_key), cas.id)

    @mock.patch("utils.k1_helper.update_content_ad", autospec=True)
    def test_ping_ad_if_relevant(self, mock_k1_ping_ad):
        ca = magic_mixer.blend(core.models.ContentAd)
        cas = magic_mixer.blend(core.models.ContentAdSource, content_ad=ca)
        cache_key = realtimechanges._get_cache_key(123)
        caches[realtimechanges.CACHE_NAME].set(cache_key, cas.id)

        realtimechanges.ping_ad_if_relevant(123)

        mock_k1_ping_ad.assert_called_once_with(cas.content_ad, msg=mock.ANY)

    @mock.patch("utils.k1_helper.update_content_ad", autospec=True)
    def test_ping_ad_if_relevant_not_present(self, mock_k1_ping_ad):
        cache_key = realtimechanges._get_cache_key(123)
        caches[realtimechanges.CACHE_NAME].delete(cache_key)
        realtimechanges.ping_ad_if_relevant(123)
        mock_k1_ping_ad.assert_not_called()
