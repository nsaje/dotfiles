import decimal

from django.conf import settings
from django.test import TestCase
from mock import patch

import core.models
import core.models.settings
import dash.constants
import dash.history_helpers
import utils.exc
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import exceptions


@patch("core.models.AdGroupSource.objects.bulk_create_on_allowed_sources")
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
@patch("utils.k1_helper.update_ad_group", autospec=True)
@patch("automation.autopilot_legacy.recalculate_budgets_ad_group", autospec=True)
@patch("django.conf.settings.HARDCODED_ACCOUNT_ID_OEN", 305)
class AdGroupCreate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.campaign = magic_mixer.blend(core.models.Campaign)

    def test_create(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        self.campaign.settings.update_unsafe(None, autopilot=True)
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

    def test_create_oen(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        campaign = magic_mixer.blend(core.models.Campaign, account__id=settings.HARDCODED_ACCOUNT_ID_OEN)
        core.models.AdGroup.objects.create(self.request, campaign)

        self.assertFalse(mock_bulk_create.called)

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

    def test_set_bidding_type(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        request_with_permission = magic_mixer.blend_request_user()
        ad_group = core.models.AdGroup.objects.create(
            request_with_permission, self.campaign, bidding_type=dash.constants.BiddingType.CPM
        )
        self.assertEqual(dash.constants.BiddingType.CPM, ad_group.bidding_type)

    def test_set_initial_bids(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_create):
        core.features.multicurrency.CurrencyExchangeRate.objects.create(
            currency=dash.constants.Currency.ILS,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("3.4930"),
        )
        account = magic_mixer.blend(core.models.Account, currency=dash.constants.Currency.ILS)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        ad_group = core.models.AdGroup.objects.create(self.request, campaign)
        self.assertEqual(decimal.Decimal("0.45"), ad_group.settings.cpc)
        self.assertEqual(1, ad_group.settings.cpm)
        self.assertEqual(decimal.Decimal("1.57185"), ad_group.settings.local_cpc)
        self.assertEqual(decimal.Decimal("3.4930"), ad_group.settings.local_cpm)

        ad_group = core.models.AdGroup.objects.create(
            self.request,
            campaign,
            initial_settings={"autopilot": dash.constants.AdGroupSettingsAutopilotState.INACTIVE},
        )
        self.assertEqual(decimal.Decimal("0.45"), ad_group.settings.cpc)
        self.assertEqual(1, ad_group.settings.cpm)
        self.assertEqual(decimal.Decimal("1.5718"), ad_group.settings.local_cpc)
        self.assertEqual(decimal.Decimal("3.4930"), ad_group.settings.local_cpm)

        ad_group = core.models.AdGroup.objects.create(
            self.request,
            campaign,
            initial_settings={"autopilot": dash.constants.AdGroupSettingsAutopilotState.INACTIVE},
            bidding_type=dash.constants.BiddingType.CPM,
        )
        self.assertEqual(decimal.Decimal("0.45"), ad_group.settings.cpc)
        self.assertEqual(1, ad_group.settings.cpm)
        self.assertEqual(decimal.Decimal("1.57185"), ad_group.settings.local_cpc)
        self.assertEqual(decimal.Decimal("3.4930"), ad_group.settings.local_cpm)


@patch("core.models.AdGroupSource.objects.bulk_clone_on_allowed_sources")
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
@patch("utils.k1_helper.update_ad_group", autospec=True)
@patch("automation.autopilot_legacy.recalculate_budgets_ad_group", autospec=True)
class AdGroupClone(TestCase):
    def test_clone(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.CONVERSION)
        source_ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign=source_campaign, bidding_type=dash.constants.BiddingType.CPM
        )

        agency = magic_mixer.blend(core.models.Agency)
        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.MOBILE)
        campaign.settings.update_unsafe(None, autopilot=True)
        direct_deal = magic_mixer.blend(core.features.deals.DirectDeal, id=1, agency=agency)

        magic_mixer.cycle(5).blend(core.features.deals.DirectDealConnection, deal=direct_deal, adgroup=source_ad_group)

        ad_group_name = "Ad Group (Clone)"
        ad_group = core.models.AdGroup.objects.clone(request, source_ad_group, campaign, ad_group_name)

        self.assertNotEqual(ad_group.pk, source_ad_group.pk)
        self.assertEqual(ad_group.campaign, campaign)
        self.assertEqual(ad_group.name, ad_group_name)
        self.assertEqual(ad_group.bidding_type, source_ad_group.bidding_type)
        self.assertEqual(ad_group.settings.state, source_ad_group.settings.state)
        self.assertEqual(5, ad_group.directdealconnection_set.count())
        self.assertEqual(5, ad_group.directdealconnection_set.filter(deal=direct_deal).count())

        self.assertTrue(mock_bulk_clone.called)
        self.assertTrue(mock_insert_adgroup.called)
        self.assertTrue(mock_autopilot_init.called)
        mock_k1_ping.assert_called_with(ad_group, msg="Campaignmodel.AdGroups.put")

        history = dash.history_helpers.get_ad_group_history(ad_group)
        self.assertEqual(len(history), 6)
        self.assertEqual(history[0].action_type, dash.constants.HistoryActionType.DEAL_CONNECTION_CREATE)
        self.assertEqual(history[5].action_type, dash.constants.HistoryActionType.SETTINGS_CHANGE)

    def test_clone_state_override(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)
        ad_group_name = "Ad Group (Clone)"
        self.assertEqual(source_ad_group.settings.state, dash.constants.AdGroupSettingsState.INACTIVE)

        ad_group = core.models.AdGroup.objects.clone(
            request,
            source_ad_group,
            source_campaign,
            ad_group_name,
            state_override=dash.constants.AdGroupSettingsState.ACTIVE,
        )
        self.assertEqual(ad_group.settings.state, dash.constants.AdGroupSettingsState.ACTIVE)

    def test_clone_video(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.VIDEO)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.VIDEO)
        campaign.settings.update_unsafe(None, autopilot=True)
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
        campaign.settings.update_unsafe(None, autopilot=True)
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

    def test_clone_bid_modifiers(self, mock_autopilot_init, mock_k1_ping, mock_insert_adgroup, mock_bulk_clone):
        request = magic_mixer.blend_request_user()

        source_campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.DISPLAY)
        source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=source_campaign)
        source = magic_mixer.blend(core.models.Source, bidder_slug="slug")

        for modifier_type in core.features.bid_modifiers.constants.BidModifierType.get_all():
            magic_mixer.blend(
                core.features.bid_modifiers.BidModifier,
                modifier=2.9,
                ad_group=source_ad_group,
                source=source
                if modifier_type
                in (
                    core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
                    core.features.bid_modifiers.constants.BidModifierType.PLACEMENT,
                )
                else None,
                type=modifier_type,
                target="9000",
            )

        campaign = magic_mixer.blend(core.models.Campaign, type=dash.constants.CampaignType.DISPLAY)

        ad_group = core.models.AdGroup.objects.clone(request, source_ad_group, campaign, "asd")

        self.assertEqual(source_ad_group.bidmodifier_set.count() - 1, ad_group.bidmodifier_set.count())
        self.assertEqual(12, ad_group.bidmodifier_set.count())
        self.assertTrue(
            1,
            source_ad_group.bidmodifier_set.filter(
                type=core.features.bid_modifiers.constants.BidModifierType.AD
            ).count(),
        )
        self.assertFalse(
            ad_group.bidmodifier_set.filter(type=core.features.bid_modifiers.constants.BidModifierType.AD).exists()
        )
