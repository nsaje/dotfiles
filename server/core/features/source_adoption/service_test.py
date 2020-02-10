import django.test

import core.models
import dash.constants
import utils.exc
from utils.magic_mixer import magic_mixer

from . import auto_add_new_ad_group_sources
from . import complete_release_shell
from . import deprecate_sources
from . import exceptions
from . import release_source
from . import unrelease_source


class SourceAdoptionCommandTest(django.test.TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        self.ad_group.settings.update_unsafe(
            None,
            b1_sources_group_enabled=True,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )
        self.source = magic_mixer.blend(core.models.Source, released=False, maintenance=False)
        magic_mixer.blend(core.models.DefaultSourceSettings, source=self.source, credentials=magic_mixer.RANDOM)
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=True)

    def test_auto_add_new_ad_group_sources_only_all_rtb(self):
        self.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=True, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )
        self.account.allowed_sources.add(self.source)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source)
        ad_group_sources = core.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(1, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(1, len(ad_group_sources))

    def test_auto_add_new_ad_group_sources_only_budget_autopilot(self):
        self.ad_group.settings.update_unsafe(
            None,
            b1_sources_group_enabled=False,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )
        self.account.allowed_sources.add(self.source)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source)
        ad_group_sources = core.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(1, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(1, len(ad_group_sources))

    def test_auto_add_new_ad_group_sources_no_allrtb_budget_autopilot(self):
        self.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=False, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )
        self.account.allowed_sources.add(self.source)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source)
        ad_group_sources = core.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_auto_add_new_ad_group_sources_not_allowed(self):
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source)
        ad_group_sources = core.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(1, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_auto_add_new_sources_false(self):
        self.account.allowed_sources.add(self.source)
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=False)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source)
        ad_group_sources = core.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_archived(self):
        self.account.allowed_sources.add(self.source)
        self.ad_group.settings.update_unsafe(self.request, archived=True)
        n_available_on, n_not_available_on = auto_add_new_ad_group_sources(self.source)
        ad_group_sources = core.models.AdGroupSource.objects.filter(ad_group=self.ad_group, source=self.source)
        self.assertEqual(0, n_available_on)
        self.assertEqual(0, n_not_available_on)
        self.assertEqual(0, len(ad_group_sources))

    def test_invalid_source_id(self):
        with self.assertRaises(utils.exc.MissingDataError):
            complete_release_shell([1234])


class SourceAdoptionTest(django.test.TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        self.source = magic_mixer.blend(core.models.Source, released=False, maintenance=False)
        magic_mixer.blend(core.models.DefaultSourceSettings, source=self.source, credentials=magic_mixer.RANDOM)
        self.account.settings.update_unsafe(self.request, auto_add_new_sources=True)

    def test_release_and_unrelease_source(self):
        n_allowed_on, n_available_on = release_source(self.request, self.source)
        self.assertTrue(self.source.released)
        self.assertEqual(1, n_allowed_on)
        self.assertEqual(0, n_available_on)
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
        n_allowed_on, n_available_on = release_source(self.request, self.source)

        self.assertTrue(self.source.released)
        self.assertEquals(0, n_allowed_on)
        self.assertEquals(0, n_available_on)
        self.assertFalse(self.source in self.account.allowed_sources.all())

    def test_auto_add_new_sources_agency_no_allowed_sources(self):
        agency = magic_mixer.blend(core.models.Agency, available_sources=[], allowed_sources=[])
        self.account.agency = agency
        self.account.save(None)

        n_allowed_on, n_available_on = release_source(self.request, self.source)
        self.assertTrue(self.source.released)
        self.assertEquals(1, n_allowed_on)
        self.assertEqual(0, n_available_on)
        self.assertTrue(self.source in self.account.allowed_sources.all())
        self.assertFalse(self.source in agency.available_sources.all())

        agency.update(None, available_sources=[self.source], allowed_sources=[])
        source2 = magic_mixer.blend(core.models.Source, released=False, maintenance=False)
        n_allowed_on, n_available_on = release_source(self.request, source2)

        self.assertTrue(self.source.released)
        self.assertEquals(0, n_allowed_on)
        self.assertEqual(1, n_available_on)
        self.assertFalse(source2 in self.account.allowed_sources.all())
        self.assertTrue(source2, agency.available_sources.all())
        self.assertFalse(source2 in agency.allowed_sources.all())

    def test_auto_add_new_sources_agency_allowed_sources(self):
        agency = magic_mixer.blend(core.models.Agency, available_sources=[self.source], allowed_sources=[self.source])
        source2 = magic_mixer.blend(core.models.Source, released=False, maintenance=False)
        self.account.agency = agency
        self.account.save(None)

        n_allowed_on, n_available_on = release_source(self.request, source2)
        self.assertTrue(source2.released)
        self.assertEquals(0, n_allowed_on)
        self.assertEquals(1, n_available_on)
        self.assertFalse(source2 in self.account.allowed_sources.all())
        self.assertTrue(source2 in self.account.agency.available_sources.all())

    def test_auto_add_new_sources_NAS_agency(self):
        agency = magic_mixer.blend(core.models.Agency, available_sources=[], allowed_sources=[])
        agency.update(None, entity_tags=["biz/NES"])
        self.account.agency = agency
        self.account.save(None)

        n_allowed_on, n_available_on = release_source(self.request, self.source)
        self.assertTrue(self.source.released)
        self.assertEquals(0, n_allowed_on)
        self.assertEqual(0, n_available_on)

        agency.update(None, available_sources=[self.source], allowed_sources=[self.source])
        source2 = magic_mixer.blend(core.models.Source, released=False, maintenance=False)
        n_allowed_on, n_available_on = release_source(self.request, source2)
        self.assertTrue(self.source.released)
        self.assertEquals(0, n_allowed_on)
        self.assertEqual(0, n_available_on)

    def test_deprecate_sources(self):
        self.account.allowed_sources.add(self.source)
        ags = core.models.AdGroupSource.objects.create(None, self.ad_group, self.source)
        ags.settings.update(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        paused = list(deprecate_sources([self.source]))
        self.assertEquals(paused[0], ags.pk)

        ags = core.models.AdGroupSource.objects.get(pk=ags.pk)
        self.assertEquals(ags.settings.state, dash.constants.AdGroupSourceSettingsState.INACTIVE)
        source = core.models.Source.objects.get(pk=self.source.pk)
        self.assertTrue(source.deprecated)
