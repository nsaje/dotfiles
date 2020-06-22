import decimal

from django.test import TestCase
from mock import patch

import core.models
import utils.exc
from core.features import bid_modifiers
from dash import constants
from utils.magic_mixer import magic_mixer

from . import exceptions


class AdGroupSourceUpdate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        self.source_type = magic_mixer.blend(
            core.models.SourceType, min_daily_budget=decimal.Decimal("0.0"), max_daily_budget=decimal.Decimal("100.0")
        )
        self.source = magic_mixer.blend(core.models.Source, source_type=self.source_type)
        self.ad_group_source = magic_mixer.blend(core.models.AdGroupSource, source=self.source, ad_group=self.ad_group)
        self.source_bid_modifier = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifiers.constants.BidModifierType.SOURCE,
            target=str(self.source.id),
            modifier=1.0,
        )

        autopilot_patcher = patch("automation.autopilot.recalculate_budgets_ad_group")
        self.recalculate_autopilot_mock = autopilot_patcher.start()
        self.addCleanup(autopilot_patcher.stop)

        k1_update_patcher = patch("utils.k1_helper.update_ad_group")
        self.k1_update_mock = k1_update_patcher.start()
        self.addCleanup(k1_update_patcher.stop)

        email_send_patcher = patch("utils.email_helper.send_ad_group_notification_email")
        self.email_send_notification_mock = email_send_patcher.start()
        self.addCleanup(email_send_patcher.stop)

    def test_update_cpc(self):
        response = self.ad_group_source.settings.update(
            self.request,
            cpc_cc=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )
        self.assertEqual(
            response,
            dict(
                cpc_cc=decimal.Decimal("1.3"),
                local_cpc_cc=decimal.Decimal("1.3"),
                daily_budget_cc=decimal.Decimal("8.2"),
                local_daily_budget_cc=decimal.Decimal("8.2"),
                state=constants.AdGroupSourceSettingsState.ACTIVE,
            ),
        )

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(self.request.user, settings.created_by)
        self.assertEqual(decimal.Decimal("1.3"), settings.cpc_cc)
        self.assertEqual(decimal.Decimal("8.2"), settings.daily_budget_cc)

        self.assertTrue(self.recalculate_autopilot_mock.called)
        self.k1_update_mock.assert_called_once_with(self.ad_group, "AdGroupSource.update")
        self.assertTrue(self.email_send_notification_mock.called)

    def test_update_cpm(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group_source.settings.update(
            self.request, cpm=decimal.Decimal("2.3"), state=constants.AdGroupSourceSettingsState.ACTIVE
        )

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(decimal.Decimal("2.3"), settings.cpm)

        self.assertTrue(self.recalculate_autopilot_mock.called)
        self.k1_update_mock.assert_called_once_with(self.ad_group, "AdGroupSource.update")
        self.assertTrue(self.email_send_notification_mock.called)

    def test_update_cpm_fail(self):
        with self.assertRaises(exceptions.CannotSetCPM):
            self.ad_group_source.settings.update(
                self.request,
                cpm=decimal.Decimal("1.3"),
                daily_budget_cc=decimal.Decimal("8.2"),
                state=constants.AdGroupSourceSettingsState.ACTIVE,
            )

    def test_update_cpc_fail(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        with self.assertRaises(exceptions.CannotSetCPC):
            self.ad_group_source.settings.update(
                self.request,
                cpc_cc=decimal.Decimal("1.3"),
                daily_budget_cc=decimal.Decimal("8.2"),
                state=constants.AdGroupSourceSettingsState.ACTIVE,
            )

    def test_update_cpm_none(self):
        old_cpm = decimal.Decimal("1.0")
        self.ad_group_source.settings.update_unsafe(None, cpm=old_cpm)
        self.ad_group_source.settings.update(
            self.request,
            cpc_cc=decimal.Decimal("1.3"),
            cpm=None,
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )
        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(decimal.Decimal("1.3"), settings.cpc_cc)
        self.assertEqual(old_cpm, settings.cpm)
        self.assertEqual(decimal.Decimal("8.2"), settings.daily_budget_cc)

    def test_update_cpc_none(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        old_cpc = decimal.Decimal("1.0")
        self.ad_group_source.settings.update_unsafe(None, cpc_cc=old_cpc)
        self.ad_group_source.settings.update(
            self.request,
            cpc_cc=None,
            cpm=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )
        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(old_cpc, settings.cpc_cc)
        self.assertEqual(decimal.Decimal("1.3"), settings.cpm)
        self.assertEqual(decimal.Decimal("8.2"), settings.daily_budget_cc)

    def test_update_no_changes(self):
        self.ad_group_source.settings.update()

        self.assertFalse(self.recalculate_autopilot_mock.called)
        self.k1_update_mock.assert_not_called()
        self.assertFalse(self.email_send_notification_mock.called)

    def test_update_skip_automation_cpc(self):
        self.ad_group_source.settings.update(
            skip_automation=True,
            cpc_cc=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertFalse(self.recalculate_autopilot_mock.called)

    def test_update_skip_automation_cpm(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group_source.settings.update(
            skip_automation=True,
            cpm=decimal.Decimal("2.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertFalse(self.recalculate_autopilot_mock.called)

    def test_update_no_autopilot(self):
        self.ad_group.settings.update_unsafe(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group_source.settings.update(
            self.request,
            cpc_cc=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )
        self.assertFalse(self.recalculate_autopilot_mock.called)

    def test_update_campaign_cpc_autopilot(self):
        self.ad_group.settings.update_unsafe(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group_source.settings.update(
            self.request,
            cpc_cc=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )
        self.assertTrue(self.recalculate_autopilot_mock.called)

    def test_update_campaign_cpm_autopilot(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.settings.update_unsafe(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)
        self.ad_group.campaign.settings.update_unsafe(None, autopilot=True)
        self.ad_group_source.settings.update(
            self.request,
            cpm=decimal.Decimal("2.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )
        self.assertTrue(self.recalculate_autopilot_mock.called)

    def test_update_no_request_cpc(self):
        self.ad_group_source.settings.update(
            system_user=constants.SystemUserType.CAMPAIGN_STOP,
            cpc_cc=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(constants.SystemUserType.CAMPAIGN_STOP, settings.system_user)

        self.assertFalse(self.email_send_notification_mock.called)

    def test_update_no_request_cpm(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group_source.settings.update(
            system_user=constants.SystemUserType.CAMPAIGN_STOP,
            cpm=decimal.Decimal("2.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(constants.SystemUserType.CAMPAIGN_STOP, settings.system_user)

        self.assertFalse(self.email_send_notification_mock.called)

    def test_update_no_k1_sync_cpc(self):
        self.ad_group_source.settings.update(
            k1_sync=False,
            cpc_cc=decimal.Decimal("1.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertFalse(self.k1_update_mock.called)

    def test_update_no_k1_sync_cpm(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group_source.settings.update(
            k1_sync=False,
            cpm=decimal.Decimal("2.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertFalse(self.k1_update_mock.called)

    def test_update_validate_cpc_not_decimal(self):
        with self.assertRaises(AssertionError):
            self.ad_group_source.settings.update(cpc_cc=0.1)

    def test_update_validate_cpm_not_decimal(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        with self.assertRaises(AssertionError):
            self.ad_group_source.settings.update(cpm=1.1)

    def test_update_skip_validation(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("1.0"), cpm=decimal.Decimal("1.6"))
        self.ad_group_source.settings.update(
            skip_validation=True,
            cpc_cc=decimal.Decimal("1.2"),
            cpm=decimal.Decimal("2.3"),
            daily_budget_cc=decimal.Decimal("8.2"),
        )

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(decimal.Decimal("1.2"), settings.cpc_cc)  # not valid setting
        self.assertEqual(decimal.Decimal("2.3"), settings.cpm)  # not valid setting
        self.assertEqual(decimal.Decimal("8.2"), settings.daily_budget_cc)

    def test_update_validate_cpc_positive(self):
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpc_cc=decimal.Decimal("-1.2"))

    def test_update_validate_cpm_positive(self):
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpm=decimal.Decimal("-2.3"))

    def test_update_validate_cpc_ad_group_cpc(self):
        self.ad_group.settings.update(None, cpc=decimal.Decimal("1.1"))

        self.ad_group_source.settings.update(cpc_cc=decimal.Decimal("1.2"))

        self.assertAlmostEqual(
            bid_modifiers.BidModifier.objects.get(
                ad_group=self.ad_group, target=str(self.ad_group_source.source.id)
            ).modifier,
            float(decimal.Decimal("1.2") / decimal.Decimal("1.1")),
            places=4,
        )

    def test_update_validate_cpm_ad_group_cpm(self):
        self.ad_group.settings.update_unsafe(None, cpm=decimal.Decimal("2.3"))

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpm=decimal.Decimal("2.4"))

    def test_update_validate_cpc_source_max_cpc(self):
        self.source_type.max_cpc = decimal.Decimal("1.1")
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpc_cc=decimal.Decimal("1.2"))

    def test_update_validate_cpm_source_max_cpm(self):
        self.source_type.max_cpm = decimal.Decimal("2.3")
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpm=decimal.Decimal("2.4"))

    def test_update_validate_cpc_source_min_cpc(self):
        self.source_type.min_cpc = decimal.Decimal("1.1")
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpc_cc=decimal.Decimal("1.0"))

    def test_update_validate_cpm_source_min_cpm(self):
        self.source_type.min_cpm = decimal.Decimal("2.3")
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(cpm=decimal.Decimal("2.2"))

    def test_update_validate_daily_budget_not_decimal(self):
        with self.assertRaises(AssertionError):
            self.ad_group_source.settings.update(daily_budget_cc=0.1)

    def test_update_validate_daily_budget_positive(self):
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(daily_budget_cc=decimal.Decimal("-1.2"))

    def test_update_validate_daily_budget_source_min(self):
        self.source_type.min_daily_budget = decimal.Decimal("2.0")
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(daily_budget_cc=decimal.Decimal("1.8"))

    def test_update_validate_daily_budget_source_max(self):
        self.source_type.max_daily_budget = decimal.Decimal("2.0")
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(daily_budget_cc=decimal.Decimal("2.2"))

    def test_update_validate_state_facebook(self):
        self.source_type.type = constants.SourceType.FACEBOOK
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

    def test_update_validate_state_yahoo(self):
        self.ad_group_source.source.source_type.min_cpc = decimal.Decimal("0.1")
        self.ad_group_source.settings.update(cpc_cc=decimal.Decimal("0.1"))
        self.ad_group.settings.update_unsafe(None, target_devices=[constants.AdTargetDevice.DESKTOP])
        self.source_type.type = constants.SourceType.YAHOO
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

    @patch("dash.views.helpers.enabling_autopilot_sources_allowed")
    def test_update_autopilot_state(self, enabling_allowed_mock):
        campaign = self.ad_group.campaign
        campaign.real_time_campaign_stop = True
        campaign.save()

        enabling_allowed_mock.return_value = False

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.settings.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

        self.ad_group_source.settings.update(state=constants.AdGroupSourceSettingsState.INACTIVE)


class MulticurrencyTest(TestCase):
    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_usd(self, mock_get_exchange_rate):
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource)
        mock_get_exchange_rate.return_value = decimal.Decimal("2.0")
        ad_group_source.settings.update(None, cpc_cc=decimal.Decimal("0.50"))
        self.assertEqual(ad_group_source.settings.local_cpc_cc, decimal.Decimal("1.00"))
        self.assertEqual(ad_group_source.settings.cpc_cc, decimal.Decimal("0.50"))

        ad_group_source.ad_group.bidding_type = constants.BiddingType.CPM
        ad_group_source.settings.update(None, cpm=decimal.Decimal("1.50"))
        self.assertEqual(ad_group_source.settings.local_cpm, decimal.Decimal("3.00"))
        self.assertEqual(ad_group_source.settings.cpm, decimal.Decimal("1.50"))

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_local(self, mock_get_exchange_rate):
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource)
        mock_get_exchange_rate.return_value = decimal.Decimal("2.0")
        ad_group_source.settings.update(None, local_cpc_cc=decimal.Decimal("0.50"))
        self.assertEqual(ad_group_source.settings.local_cpc_cc, decimal.Decimal("0.50"))
        self.assertEqual(ad_group_source.settings.cpc_cc, decimal.Decimal("0.25"))

        ad_group_source.ad_group.bidding_type = constants.BiddingType.CPM
        ad_group_source.settings.update(None, local_cpm=decimal.Decimal("2.00"))
        self.assertEqual(ad_group_source.settings.local_cpm, decimal.Decimal("2.00"))
        self.assertEqual(ad_group_source.settings.cpm, decimal.Decimal("1.00"))

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_set_none(self, mock_get_exchange_rate):
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource)
        mock_get_exchange_rate.return_value = decimal.Decimal("2.0")
        ad_group_source.settings.update(None, state=2)
        mock_get_exchange_rate.assert_not_called()
