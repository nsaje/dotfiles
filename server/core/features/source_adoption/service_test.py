import django.test

import dash.models

from utils.magic_mixer import magic_mixer
import utils.exc

from . import auto_add_new_ad_group_sources
from . import release_source
from . import unrelease_source
from . import exceptions


class SourceAdoptionCommandTest(django.test.TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(dash.models.Account)
        campaign = magic_mixer.blend(dash.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        self.source = magic_mixer.blend(dash.models.Source, id=0, released=False, maintenance=False)
        magic_mixer.blend(dash.models.DefaultSourceSettings, source=self.source, credentials=magic_mixer.RANDOM)
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=True)

    def test_auto_add_new_ad_group_sources(self):
        self.account.allowed_sources.add(self.source)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source.id)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(1, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(1, len(ad_group_sources))

    def test_auto_add_new_ad_group_sources_not_allowed(self):
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source.id)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(1, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_auto_add_new_sources_false(self):
        self.account.allowed_sources.add(self.source)
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=False)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source.id)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_archived(self):
        self.account.allowed_sources.add(self.source)
        self.ad_group.settings.update_unsafe(self.request, archived=True)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source.id)
        ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_invalid_source_id(self):
        with self.assertRaises(utils.exc.MissingDataError):
            auto_add_new_ad_group_sources(1234)


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
        n_allowed_on = release_source(self.request, self.source)
        self.assertTrue(self.source.released)
        self.assertEqual(1, n_allowed_on)
        self.assertTrue(self.source in self.account.allowed_sources.all())

        n_allowed_on = unrelease_source(self.request, self.source)
        self.assertFalse(self.source.released)
        self.assertIsNone(n_allowed_on)
        self.assertTrue(self.source in self.account.allowed_sources.all())

    def test_already_released(self):
        self.source.released = True
        self.source.save()
        with self.assertRaises(exceptions.SourceAlreadyReleased):
            release_source(self.request, self.source)

    def test_already_unreleased(self):
        with self.assertRaises(exceptions.SourceAlreadyUnreleased):
            unrelease_source(self.request, self.source)

    def test_auto_add_new_sources_false(self):
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=False)
        n_allowed_on = release_source(self.request, self.source)
        self.assertTrue(self.source.released)
        self.assertEquals(0, n_allowed_on)
        self.assertFalse(self.source in self.account.allowed_sources.all())
