from django.test import TestCase

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer


class CreateContentAdSource(TestCase):
    def test_create(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, state=constants.ContentAdSourceState.ACTIVE)
        source = magic_mixer.blend(core.models.Source)

        content_ad_source = core.models.ContentAdSource.objects.create(content_ad, source)

        self.assertEqual(content_ad_source.state, content_ad.state)
        self.assertEqual(content_ad_source.content_ad, content_ad)
        self.assertEqual(content_ad_source.source, source)

    def test_bulk_create(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, state=constants.ContentAdSourceState.ACTIVE)
        sources = magic_mixer.cycle(5).blend(core.models.Source)

        content_ad_sources = core.models.ContentAdSource.objects.bulk_create(content_ad, sources)

        self.assertEqual(len(content_ad_sources), 5)
        self.assertEqual([x.state for x in content_ad_sources], 5 * [content_ad.state])
        self.assertCountEqual([x.source for x in content_ad_sources], list(sources))
        self.assertEqual([x.content_ad for x in content_ad_sources], 5 * [content_ad])
