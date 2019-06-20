from django.test import TestCase
from mock import patch

import core.models
import core.models.settings
import dash.constants
import dash.history_helpers
import utils.exc
from utils.magic_mixer import magic_mixer

from . import exceptions


@patch("core.models.AdGroupSource.objects.bulk_create_on_allowed_sources")
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
@patch("utils.k1_helper.update_ad_group", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
class AdGroupCreate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.campaign = magic_mixer.blend(core.models.Campaign)

    def test_create(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        self.assertEqual(0, core.models.settings.AdGroupSettings.objects.all().count())

        ad_group = core.models.AdGroup.objects.create(self.request, self.campaign)

        self.assertIsNotNone(ad_group.get_current_settings().pk)
        self.assertEqual(ad_group.campaign, self.campaign)

        self.assertTrue(mock_bulk_create.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group, msg="Campaignmodel.AdGroups.put")

        history = dash.history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, dash.constants.HistoryActionType.SETTINGS_CHANGE)

    def test_create_campaign_archived(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        self.campaign.archived = True
        with self.assertRaises(exceptions.CampaignIsArchived):
            core.models.AdGroup.objects.create(self.request, self.campaign, name="test")

    @patch("django.conf.settings.AMPLIFY_REVIEW", True)
    @patch("core.models.AdGroupSource.objects.create")
    def test_create_amplify_review_ad_group_source(
        self, mock_create, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create
    ):
        outbrain_source = magic_mixer.blend(core.models.Source, source_type__type="outbrain")
        ad_group = core.models.AdGroup.objects.create(self.request, self.campaign)
        mock_create.assert_called_with(
            self.request,
            ad_group,
            outbrain_source,
            write_history=False,
            k1_sync=False,
            ad_review_only=True,
            skip_notification=True,
            state=dash.constants.AdGroupSourceSettingsState.INACTIVE,
        )


@patch("core.models.AdGroupSource.objects.bulk_clone_on_allowed_sources")
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
@patch("utils.k1_helper.update_ad_group", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
class AdGroupClone(TestCase):
    def test_clone(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.CONVERSION)
        source_ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign=source_campaign, bidding_type=dash.constants.BiddingType.CPM
        )

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.MOBILE)

        ad_group_name = "Ad Group (Clone)"
        ad_group = core.models.AdGroup.objects.clone(request, source_ad_group, campaign, ad_group_name)

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, ad_group_name)
        self.assertEqual(ad_group.bidding_type, source_ad_group.bidding_type)

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group, msg="Campaignmodel.AdGroups.put")

        history = dash.history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, dash.constants.HistoryActionType.SETTINGS_CHANGE)

    def test_clone_video(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.VIDEO)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.VIDEO)
        ad_group = core.models.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, "asd")

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group, msg="Campaignmodel.AdGroups.put")

        history = dash.history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, dash.constants.HistoryActionType.SETTINGS_CHANGE)

    def test_clone_video_error(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.VIDEO)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.CONTENT)
        with self.assertRaises(utils.exc.ValidationError):
            core.models.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")

    def test_clone_display(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.DISPLAY)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.DISPLAY)
        ad_group = core.models.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, "asd")

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group, msg="Campaignmodel.AdGroups.put")

        history = dash.history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action_type, dash.constants.HistoryActionType.SETTINGS_CHANGE)

    def test_clone_display_error(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.DISPLAY)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.CONTENT)
        with self.assertRaises(utils.exc.ValidationError):
            core.models.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")
