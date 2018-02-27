from mock import patch
from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants
from dash import history_helpers

import core.entity


@patch.object(core.entity.AdGroupSource.objects, 'bulk_create_on_allowed_sources')
@patch('utils.redirector_helper.insert_adgroup', autospec=True)
@patch('utils.k1_helper.update_ad_group', autospec=True)
@patch('automation.autopilot.initialize_budget_autopilot_on_ad_group', autospec=True)
class AdGroupCreate(TestCase):

    def test_create(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.entity.Campaign)
        self.assertEqual(0, core.entity.settings.AdGroupSettings.objects.all().count())

        ad_group = core.entity.AdGroup.objects.create(request, campaign)

        self.assertIsNotNone(ad_group.get_current_settings().pk)
        self.assertEqual(ad_group.campaign, campaign)

        self.assertTrue(mock_bulk_create.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group.id, msg='CampaignAdGroups.put')

        history = history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.SETTINGS_CHANGE)


@patch.object(core.entity.AdGroupSource.objects, 'bulk_clone_on_allowed_sources')
@patch('utils.redirector_helper.insert_adgroup', autospec=True)
@patch('utils.k1_helper.update_ad_group', autospec=True)
@patch('automation.autopilot.initialize_budget_autopilot_on_ad_group', autospec=True)
class AdGroupClone(TestCase):

    def test_clone(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_ad_group = magic_mixer.blend(core.entity.AdGroup)

        campaign = magic_mixer.blend(core.entity.Campaign)
        ad_group = core.entity.AdGroup.objects.clone(request, source_ad_group, campaign, 'asd')

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, 'asd')

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group.id, msg='CampaignAdGroups.put')

        history = history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.SETTINGS_CHANGE)


class AdGroupHistory(TestCase):

    def test_history_ad_group_created(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.AdGroupSource, ad_group=ad_group)

        ad_group.write_history_created(request)

        history = history_helpers.get_ad_group_history(ad_group)

        self.assertEqual(len(history), 7)
        self.assertRegex(
            history.first().changes_text,
            r'Created settings and automatically created campaigns for 5 sources .*')
