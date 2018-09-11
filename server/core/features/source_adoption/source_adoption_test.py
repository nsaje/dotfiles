import django.test

import dash.models
from utils.magic_mixer import magic_mixer

from . import source_adoption
from . import exceptions


class SourceAdoptionTest(django.test.TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(dash.models.Account)
        campaign = magic_mixer.blend(dash.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        self.source = magic_mixer.blend(dash.models.Source, released=False, maintenance=False)
        magic_mixer.blend(dash.models.DefaultSourceSettings, source=self.source, credentials=magic_mixer.RANDOM)
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=True)

    def test_release_and_unrelease_source(self):
        count = source_adoption.release_source(self.request, self.source)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertTrue(self.source.released)
        self.assertEqual(1, count)
        self.assertEqual(1, len(ad_group_sources))
        self.assertTrue(self.source in self.account.allowed_sources.all())

        count = source_adoption.unrelease_source(self.request, self.source)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertFalse(self.source.released)
        self.assertEqual(0, count)
        self.assertEqual(1, len(ad_group_sources))
        self.assertTrue(self.source in self.account.allowed_sources.all())

    def test_already_released(self):
        self.source.released = True
        self.source.save()
        with self.assertRaises(exceptions.SourceAlreadyReleased):
            source_adoption.release_source(self.request, self.source)

    def test_already_unreleased(self):
        with self.assertRaises(exceptions.SourceAlreadyUnreleased):
            source_adoption.unrelease_source(self.request, self.source)

    def test_auto_add_new_sources_false(self):
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=False)
        count = source_adoption.release_source(self.request, self.source)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertTrue(self.source.released)
        self.assertEqual(0, count)
        self.assertEqual(0, len(ad_group_sources))
        self.assertFalse(self.source in self.account.allowed_sources.all())
