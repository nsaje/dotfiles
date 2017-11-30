import decimal
from mock import patch

from django.test import TestCase
from utils.magic_mixer import magic_mixer
from dash import constants

import core.entity
import core.source

import utils.exc


@patch('utils.k1_helper.update_ad_group')
@patch('dash.views.helpers.get_source_initial_state', lambda x: True)
class AdGroupSourceCreate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.default_source_settings = magic_mixer.blend(
            core.source.DefaultSourceSettings,
            source__maintenance=False,
            credentials=magic_mixer.RANDOM,
        )
        self.ad_group = magic_mixer.blend(
            core.entity.AdGroup,
            campaign__account__allowed_sources=[self.default_source_settings.source],
        )

    def test_create(self, mock_k1):
        ad_group_source = core.entity.AdGroupSource.objects.create(
            self.request, self.ad_group, self.default_source_settings.source)

        self.assertEqual(ad_group_source.source, self.default_source_settings.source)
        self.assertTrue(mock_k1.called)

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source=ad_group_source).group_current_settings()
        self.assertEqual([x.state for x in ad_group_source_settings], [constants.AdGroupSourceSettingsState.ACTIVE])

    def test_create_with_update(self, mock_k1):
        ad_group_source = core.entity.AdGroupSource.objects.create(
            self.request,
            self.ad_group,
            self.default_source_settings.source,
            state=constants.AdGroupSourceSettingsState.INACTIVE,
            cpc_cc=decimal.Decimal('0.13'),
            daily_budget_cc=decimal.Decimal('5.2'),
        )

        self.assertEqual(ad_group_source.source, self.default_source_settings.source)
        self.assertTrue(mock_k1.called)

        new_settings = ad_group_source.get_current_settings()
        self.assertEqual(constants.AdGroupSourceSettingsState.INACTIVE, new_settings.state)
        self.assertEqual(decimal.Decimal('0.13'), new_settings.cpc_cc)
        self.assertEqual(decimal.Decimal('5.2'), new_settings.daily_budget_cc)

    def test_create_already_exists(self, mock_k1):
        magic_mixer.blend(
            core.entity.AdGroupSource,
            ad_group=self.ad_group,
            source=self.default_source_settings.source,
        )

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(
                self.request, self.ad_group, self.default_source_settings.source)

    def test_create_not_on_account(self, mock_k1):
        self.ad_group.campaign.account.allowed_sources.remove(self.default_source_settings.source)

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(
                self.request, self.ad_group, self.default_source_settings.source)

    @patch('dash.retargeting_helper.can_add_source_with_retargeting')
    def test_create_retargeting(self, mock_retargeting, mock_k1):
        mock_retargeting.return_value = False

        with self.assertRaises(utils.exc.ValidationError):
            core.entity.AdGroupSource.objects.create(
                self.request, self.ad_group, self.default_source_settings.source)

        mock_retargeting.assert_called_once_with(self.default_source_settings.source, self.ad_group.get_current_settings())

    def test_bulk_create_on_allowed_sources(self, mock_k1):
        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            self.request, self.ad_group, write_history=False)

        self.assertEqual([x.source for x in ad_group_sources], [self.default_source_settings.source])
        self.assertTrue(mock_k1.called)

        ad_group_source_settings = core.entity.settings.AdGroupSourceSettings.objects.filter(
            ad_group_source__ad_group=self.ad_group).group_current_settings()
        self.assertEqual([x.state for x in ad_group_source_settings], [constants.AdGroupSourceSettingsState.ACTIVE])

    def test_bulk_create_on_allowed_sources_maintenance(self, mock_k1):
        self.default_source_settings.source.maintenance = True
        self.default_source_settings.source.save()
        request = magic_mixer.blend_request_user()

        ad_group_sources = core.entity.AdGroupSource.objects.bulk_create_on_allowed_sources(
            request, self.ad_group, write_history=False)

        self.assertItemsEqual(ad_group_sources, [])
        self.assertFalse(mock_k1.called)


@patch('utils.k1_helper.update_ad_group')
class AdGroupSourceClone(TestCase):

    def setUp(self):
        self.request = magic_mixer.blend_request_user()

    def test_clone(self, mock_k1):
        source_ad_group_source = magic_mixer.blend(core.entity.AdGroupSource,
                                                   source=magic_mixer.blend_source_w_defaults())
        source_ad_group_source.settings.update_unsafe(
            None,
            daily_budget_cc=decimal.Decimal('5'),
            cpc_cc=decimal.Decimal('0.1'),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        ad_group = magic_mixer.blend(core.entity.AdGroup)

        ad_group_source = core.entity.AdGroupSource.objects.clone(
            magic_mixer.blend_request_user(), ad_group, source_ad_group_source)

        ad_group_source_settings = ad_group_source.get_current_settings()
        self.assertEqual(ad_group_source.source, source_ad_group_source.source)
        self.assertEqual(ad_group_source_settings.daily_budget_cc, source_ad_group_source.settings.daily_budget_cc)
        self.assertEqual(ad_group_source_settings.cpc_cc, source_ad_group_source.settings.cpc_cc)

        self.assertTrue(mock_k1.called)


class AdGroupSourceUpdate(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.ad_group = magic_mixer.blend(core.entity.AdGroup)
        self.source_type = magic_mixer.blend(core.source.SourceType)
        self.source = magic_mixer.blend(
            core.source.Source,
            source_type=self.source_type,
        )
        self.ad_group_source = magic_mixer.blend(
            core.entity.AdGroupSource,
            source=self.source,
            ad_group=self.ad_group,
        )

        autopilot_plus_patcher = patch('automation.autopilot_plus')
        self.autopilot_mock = autopilot_plus_patcher.start()
        self.addCleanup(autopilot_plus_patcher.stop)

        k1_update_patcher = patch('utils.k1_helper.update_ad_group')
        self.k1_update_mock = k1_update_patcher.start()
        self.addCleanup(k1_update_patcher.stop)

        email_send_patcher = patch('utils.email_helper.send_ad_group_notification_email')
        self.email_send_notification_mock = email_send_patcher.start()
        self.addCleanup(email_send_patcher.stop)

    def test_update(self):
        response = self.ad_group_source.update(
            self.request,
            cpc_cc=decimal.Decimal('1.3'),
            daily_budget_cc=decimal.Decimal('8.2'),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertIn('autopilot_changed_sources_text', response)

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(self.request.user, settings.created_by)
        self.assertEqual(decimal.Decimal('1.3'), settings.cpc_cc)
        self.assertEqual(decimal.Decimal('8.2'), settings.daily_budget_cc)
        self.assertEqual(constants.AdGroupSourceSettingsState.ACTIVE, settings.state)

        self.assertTrue(self.autopilot_mock.initialize_budget_autopilot_on_ad_group.called)
        self.k1_update_mock.assert_called_once_with(self.ad_group.id, 'AdGroupSource.update')
        self.assertTrue(self.email_send_notification_mock.called)

    def test_update_no_changes(self):
        response = self.ad_group_source.update()

        self.assertIn('autopilot_changed_sources_text', response)

        self.assertFalse(self.autopilot_mock.initialize_budget_autopilot_on_ad_group.called)
        self.k1_update_mock.assert_not_called()
        self.assertFalse(self.email_send_notification_mock.called)

    def test_update_skip_automation(self):
        self.ad_group_source.update(
            skip_automation=True,
            cpc_cc=decimal.Decimal('1.3'),
            daily_budget_cc=decimal.Decimal('8.2'),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertFalse(self.autopilot_mock.initialize_budget_autopilot_on_ad_group.called)

    def test_update_no_request(self):
        self.ad_group_source.update(
            system_user=constants.SystemUserType.CAMPAIGN_STOP,
            cpc_cc=decimal.Decimal('1.3'),
            daily_budget_cc=decimal.Decimal('8.2'),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(constants.SystemUserType.CAMPAIGN_STOP, settings.system_user)

        self.assertFalse(self.email_send_notification_mock.called)

    def test_update_no_k1_sync(self):
        self.ad_group_source.update(
            k1_sync=False,
            cpc_cc=decimal.Decimal('1.3'),
            daily_budget_cc=decimal.Decimal('8.2'),
            state=constants.AdGroupSourceSettingsState.ACTIVE,
        )

        self.assertFalse(self.k1_update_mock.called)

    def test_update_validate_cpc_not_decimal(self):
        with self.assertRaises(AssertionError):
            self.ad_group_source.update(cpc_cc=0.1)

    def test_update_skip_validation(self):
        self.ad_group_source.update(skip_validation=True,
                                    cpc_cc=decimal.Decimal('-1.2'),
                                    daily_budget_cc=decimal.Decimal('8.2'),)

        settings = self.ad_group_source.get_current_settings()
        self.assertEqual(decimal.Decimal('-1.2'), settings.cpc_cc)  # not valid setting
        self.assertEqual(decimal.Decimal('8.2'), settings.daily_budget_cc)

    def test_update_validate_cpc_positive(self):
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(cpc_cc=decimal.Decimal('-1.2'))

    def test_update_validate_cpc_ad_group_max_cpc(self):
        self.ad_group.settings.update_unsafe(None, cpc_cc=1.1)

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(cpc_cc=decimal.Decimal('1.2'))

    def test_update_validate_cpc_source_max_cpc(self):
        self.source_type.max_cpc = 1.1
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(cpc_cc=decimal.Decimal('1.2'))

    def test_update_validate_cpc_source_min_cpc(self):
        self.source_type.min_cpc = 1.1
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(cpc_cc=decimal.Decimal('1.0'))

    def test_update_validate_cpc_constraints(self):
        magic_mixer.blend(core.entity.settings.CpcConstraint, ad_group=self.ad_group, source=self.source, min_cpc=1.1)
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(cpc_cc=decimal.Decimal('1.0'))

    def test_update_validate_daily_budget_not_decimal(self):
        with self.assertRaises(AssertionError):
            self.ad_group_source.update(daily_budget_cc=0.1)

    def test_update_validate_daily_budget_positive(self):
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(daily_budget_cc=decimal.Decimal('-1.2'))

    def test_update_validate_daily_budget_source_min(self):
        self.source_type.min_daily_budget = 2.0
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(daily_budget_cc=decimal.Decimal('1.8'))

    def test_update_validate_daily_budget_source_max(self):
        self.source_type.max_daily_budget = 2.0
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(daily_budget_cc=decimal.Decimal('2.2'))

    def test_update_validate_state_retargeting(self):
        self.ad_group.settings.update_unsafe(None, retargeting_ad_groups=[1])
        self.source.supports_retargeting = False
        self.source.supports_retargeting_manually = False
        self.source.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

    def test_update_validate_state_facebook(self):
        self.source_type.type = constants.SourceType.FACEBOOK
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

    def test_update_validate_state_yahoo(self):
        self.ad_group_source.update(cpc_cc=decimal.Decimal('0.1'))
        self.ad_group.settings.update_unsafe(None, target_devices=[constants.AdTargetDevice.DESKTOP])
        self.source_type.type = constants.SourceType.YAHOO
        self.source_type.save()
        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

    def test_update_landing_mode(self):
        self.ad_group.campaign.settings.update(None, landing_mode=True)

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(daily_budget_cc=decimal.Decimal('0.1'))

        self.ad_group_source.update(cpc_cc=decimal.Decimal('0.1'))

    @patch('automation.campaign_stop.get_max_settable_source_budget')
    def test_update_campaign_stop_budget(self, get_budget_mock):
        self.ad_group.campaign.settings.update(None, automatic_campaign_stop=True)

        get_budget_mock.return_value = decimal.Decimal('1.0')

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(daily_budget_cc=decimal.Decimal('1.1'))

        self.ad_group_source.update(daily_budget_cc=decimal.Decimal('1.0'))

    @patch('automation.campaign_stop.can_enable_media_source')
    def test_update_campaign_stop_state(self, can_enable_mock):
        self.ad_group.campaign.settings.update(None, automatic_campaign_stop=True)

        can_enable_mock.return_value = False

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

    @patch('dash.views.helpers.enabling_autopilot_sources_allowed')
    def test_update_autopilot_state(self, enabling_allowed_mock):
        self.ad_group.campaign.settings.update(None, automatic_campaign_stop=True)

        enabling_allowed_mock.return_value = False

        with self.assertRaises(utils.exc.ValidationError):
            self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.ACTIVE)

        self.ad_group_source.update(state=constants.AdGroupSourceSettingsState.INACTIVE)


class MigrateToBcmV2Test(TestCase):

    def test_migrate_to_bcm_v2(self):
        account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        campaign = magic_mixer.blend(core.entity.Campaign, account=account)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)
        ad_group_source = magic_mixer.blend(core.entity.AdGroupSource, ad_group=ad_group)

        request = magic_mixer.blend_request_user()
        ad_group_source.update(
            request=request,
            k1_sync=False,
            system_user=None,
            skip_automation=True,
            skip_validation=True,
            skip_notification=True,
            daily_budget_cc=decimal.Decimal('10'),
            cpc_cc=decimal.Decimal('0.32'),
        )

        request = magic_mixer.blend_request_user(permissions=['can_set_ad_group_max_cpm'])
        ad_group_source.migrate_to_bcm_v2(request, decimal.Decimal('0.2'), decimal.Decimal('0.1'))

        ad_group_source_settings = ad_group_source.get_current_settings()
        self.assertEqual(14, ad_group_source_settings.daily_budget_cc)
        self.assertEqual(decimal.Decimal('0.444'), ad_group_source_settings.cpc_cc)
