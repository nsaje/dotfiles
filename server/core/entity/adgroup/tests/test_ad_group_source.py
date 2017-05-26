from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer
from dash import constants

import core.entity
import core.source


@patch('utils.k1_helper.update_ad_group')
@patch('dash.views.helpers.get_source_initial_state', lambda x: True)
class AdGroupSourceCreate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    def test_create(self, mock_k1):
        default_source_settings = magic_mixer.blend(
            core.source.DefaultSourceSettings, source__maintenance=False, credentials=magic_mixer.RANDOM)
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        ad_group_source = core.entity.AdGroupSource.objects.create(
            self.request, ad_group, default_source_settings.source)

        self.assertEqual(ad_group_source.source, default_source_settings.source)
        self.assertTrue(mock_k1.called)

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source).group_current_settings()
        self.assertEqual([x.state for x in ad_group_source_settings], [constants.AdGroupSourceSettingsState.ACTIVE])

    def test_bulk_create_on_allowed_sources(self, mock_k1):
        default_source_settings = magic_mixer.blend(
            core.source.DefaultSourceSettings, source__maintenance=False, credentials=magic_mixer.RANDOM)
        account = magic_mixer.blend(core.entity.Account, allowed_sources=[default_source_settings.source])
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign__account=account)

        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            self.request, ad_group, write_history=False)

        self.assertEqual([x.source for x in ad_group_sources], [default_source_settings.source])
        self.assertTrue(mock_k1.called)

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=ad_group).group_current_settings()
        self.assertEqual([x.state for x in ad_group_source_settings], [constants.AdGroupSourceSettingsState.ACTIVE])

    def test_bulk_create_on_allowed_sources_maintenance(self, mock_k1):
        default_source_settings = magic_mixer.blend(
            core.source.DefaultSourceSettings,
            source__maintenance=True,
            credentials=magic_mixer.RANDOM)
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.entity.Account, allowed_sources=[default_source_settings.source])
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign__account=account)

        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            request, ad_group, write_history=False)

        self.assertItemsEqual(ad_group_sources, [])
        self.assertFalse(mock_k1.called)


@patch('utils.k1_helper.update_ad_group')
class AdGroupSourceClone(TestCase):

    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    def test_clone(self, mock_k1):
        source_ad_group_source = magic_mixer.blend(core.entity.AdGroupSource,
                                                   source=magic_mixer.blend_source_w_defaults())
        source_ad_group_source_settings = magic_mixer.blend_latest_settings(
            source_ad_group_source,
            daily_budget_cc=magic_mixer.RANDOM, cpc_cc=magic_mixer.RANDOM, state=magic_mixer.RANDOM)

        ad_group = magic_mixer.blend(core.entity.AdGroup)

        ad_group_source = core.entity.AdGroupSource.objects.clone(
            magic_mixer.blend_request_user(), ad_group, source_ad_group_source)

        ad_group_source_settings = ad_group_source.get_current_settings()
        self.assertEqual(ad_group_source.source, source_ad_group_source.source)
        self.assertEqual(ad_group_source_settings.daily_budget_cc, source_ad_group_source_settings.daily_budget_cc)
        self.assertEqual(ad_group_source_settings.cpc_cc, source_ad_group_source_settings.cpc_cc)

        self.assertTrue(mock_k1.called)

    def test_bulk_clone_on_allowed_sources(self, mock_k1):
        default_source_settings = magic_mixer.cycle(5).blend(
            core.source.DefaultSourceSettings, source__maintenance=False, credentials=magic_mixer.RANDOM)
        source_ad_group = magic_mixer.blend(core.entity.AdGroup)
        # sources: 0, 1, 2
        source_ad_group_sources = [
            magic_mixer.blend(core.entity.AdGroupSource, source=x.source, ad_group=source_ad_group)
            for x in default_source_settings[:3]]

        for x in source_ad_group_sources:
            magic_mixer.blend_latest_settings(x, daily_budget_cc=magic_mixer.RANDOM)

        # sources: 0, 1, 4
        allowed_sources = [x.source for x in default_source_settings[:2]] + [default_source_settings[4].source]
        account = magic_mixer.blend(core.entity.Account, allowed_sources=allowed_sources)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign__account=account)

        ad_group_sources = core.entity.AdGroupSource.objects.bulk_clone_on_allowed_sources(
            self.request, ad_group, source_ad_group, write_history=False)

        self.assertItemsEqual([x.source for x in ad_group_sources], allowed_sources)

        # get sources that should be copied (0 and 1)
        cloned_sources = [x.source for x in default_source_settings[:2]]
        daily_budgets = [x.get_current_settings().daily_budget_cc for x in ad_group_sources
                         if x.source in cloned_sources]
        source_daily_budgets = [x.get_current_settings().daily_budget_cc for x in source_ad_group_sources
                                if x.source in cloned_sources]
        self.assertItemsEqual(daily_budgets, source_daily_budgets)
        self.assertTrue(mock_k1.called)
