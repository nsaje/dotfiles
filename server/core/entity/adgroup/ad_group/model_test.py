from mock import patch
from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash import constants
from dash import history_helpers

import core.entity
import core.source

import utils.exc


@patch.object(core.entity.AdGroupSource.objects, "bulk_create_on_allowed_sources")
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
@patch("utils.k1_helper.update_ad_group", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
class AdGroupCreate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.campaign = magic_mixer.blend(core.entity.Campaign)

    def test_create(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        self.assertEqual(0, core.entity.settings.AdGroupSettings.objects.all().count())

        ad_group = core.entity.AdGroup.objects.create(self.request, self.campaign)

        self.assertIsNotNone(ad_group.get_current_settings().pk)
        self.assertEqual(ad_group.campaign, self.campaign)

        self.assertTrue(mock_bulk_create.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group.id, msg="CampaignAdGroups.put")

        history = history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.SETTINGS_CHANGE)

    @patch("django.conf.settings.AMPLIFY_REVIEW", True)
    @patch.object(core.entity.AdGroupSource.objects, "create")
    def test_create_amplify_review_ad_group_source(
        self, mock_create, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create
    ):
        outbrain_source = magic_mixer.blend(core.source.Source, source_type__type="outbrain")
        ad_group = core.entity.AdGroup.objects.create(self.request, self.campaign)
        mock_create.assert_called_with(
            self.request,
            ad_group,
            outbrain_source,
            write_history=False,
            k1_sync=False,
            ad_review_only=True,
            state=constants.AdGroupSourceSettingsState.INACTIVE,
        )


@patch.object(core.entity.AdGroupSource.objects, "bulk_clone_on_allowed_sources")
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
@patch("utils.k1_helper.update_ad_group", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
class AdGroupClone(TestCase):
    def test_clone(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.entity.Campaign, type=constants.CampaignType.CONVERSION)
        source_ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.entity.Campaign, type=constants.CampaignType.MOBILE)
        ad_group = core.entity.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, "asd")

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group.id, msg="CampaignAdGroups.put")

        history = history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.SETTINGS_CHANGE)

    def test_clone_video(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.entity.Campaign, type=constants.CampaignType.VIDEO)
        source_ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.entity.Campaign, type=constants.CampaignType.VIDEO)
        ad_group = core.entity.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, "asd")

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group.id, msg="CampaignAdGroups.put")

        history = history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.SETTINGS_CHANGE)

    def test_clone_video_error(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.entity.Campaign, type=constants.CampaignType.VIDEO)
        source_ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.entity.Campaign, type=constants.CampaignType.CONTENT)
        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")


class AdGroupHistory(TestCase):
    def test_history_ad_group_created(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.AdGroupSource, ad_group=ad_group)

        ad_group.write_history_created(request)

        history = history_helpers.get_ad_group_history(ad_group)

        self.assertEqual(len(history), 7)
        self.assertRegex(
            history.first().changes_text, r"Created settings and automatically created campaigns for 5 sources .*"
        )
