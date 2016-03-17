import datetime
import decimal
from mock import patch

from django import test

from dash import models
from dash import constants
from dash import consistency


class SettingsStateConsistencyTestCase(test.TestCase):
    fixtures = ['test_models', 'test_consistency']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(pk=1)
        self.settings_state_consistency = consistency.SettingsStateConsistence(self.ad_group_source)

    @patch('dash.consistency.SettingsStateConsistence._get_latest_state')
    def test_is_consistent_equivalent_state(self, mock_get_latest_state):
        state = models.AdGroupSourceState.objects.get(pk=1)
        mock_get_latest_state.return_value = state
        consistent = self.settings_state_consistency.is_consistent()
        self.assertTrue(consistent)

    @patch('dash.consistency.SettingsStateConsistence._get_latest_state')
    def test_is_consistent_different_state(self, mock_get_latest_state):
        state = models.AdGroupSourceState.objects.get(pk=2)
        mock_get_latest_state.return_value = state
        consistent = self.settings_state_consistency.is_consistent()
        self.assertFalse(consistent)

    @patch('dash.consistency.SettingsStateConsistence._get_latest_state')
    def test_is_consistent_equivalent_and_older_state(self, mock_get_latest_state):
        settings = self.ad_group_source.get_current_settings()
        state = models.AdGroupSourceState.objects.get(pk=2)
        state.created_dt = settings.created_dt - datetime.timedelta(days=1)
        mock_get_latest_state.return_value = state
        consistent = self.settings_state_consistency.is_consistent()
        self.assertTrue(consistent)

    @patch('dash.consistency.SettingsStateConsistence._get_latest_state')
    def test_is_consistent_no_state(self, mock_get_latest_state):
        state = None
        mock_get_latest_state.return_value = state
        consistent = self.settings_state_consistency.is_consistent()
        self.assertTrue(consistent)

    def test_get_needed_state_updates(self):
        changes = self.settings_state_consistency.get_needed_state_updates()
        settings = self.ad_group_source.get_current_settings()
        self.assertDictEqual(changes, {'daily_budget_cc': settings.daily_budget_cc,
                                       'cpc_cc': settings.cpc_cc,
                                       'state': constants.AdGroupSourceSettingsState.ACTIVE,
                                       })

    def test_get_needed_state_updates_with_adgroup_inactive(self):
        ad_group_settings = self.ad_group_source.ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.state = constants.AdGroupSettingsState.INACTIVE
        new_ad_group_settings.save(None)

        changes = self.settings_state_consistency.get_needed_state_updates()
        settings = self.ad_group_source.get_current_settings()
        self.assertDictEqual(changes, {'daily_budget_cc': settings.daily_budget_cc,
                                       'cpc_cc': settings.cpc_cc
                                       })

    def test_get_state_changes(self):
        state = models.AdGroupSourceState.objects.get(pk=1)
        settings = models.AdGroupSourceSettings.objects.get(pk=1)
        changes = self.settings_state_consistency._get_state_changes(state, settings)
        self.assertEqual(changes, {})

        state.daily_budget_cc = decimal.Decimal(0.1)
        changes = self.settings_state_consistency._get_state_changes(state, settings)
        self.assertEqual(changes['daily_budget_cc'], settings.daily_budget_cc)
        self.assertNotIn('cpc_cc', changes)
        self.assertNotIn('state', changes)

        state = models.AdGroupSourceState.objects.get(pk=2)
        changes = self.settings_state_consistency._get_state_changes(state, settings)
        self.assertEqual(changes['cpc_cc'], settings.cpc_cc)
        self.assertEqual(changes['daily_budget_cc'], settings.daily_budget_cc)
        self.assertEqual(changes['state'], settings.state)

    def test_get_actual_source_settings_state(self):
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)

        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
        actual_state = self.settings_state_consistency._get_actual_source_settings_state(ad_group_source_settings)
        self.assertEqual(actual_state, constants.AdGroupSourceSettingsState.INACTIVE)

        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
        actual_state = self.settings_state_consistency._get_actual_source_settings_state(ad_group_source_settings)
        self.assertEqual(actual_state, constants.AdGroupSourceSettingsState.ACTIVE)

        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
        ad_group_settings_copy = ad_group_settings.copy_settings()
        ad_group_settings_copy.state = constants.AdGroupSettingsState.INACTIVE
        ad_group_settings_copy.save(None)
        actual_state = self.settings_state_consistency._get_actual_source_settings_state(ad_group_source_settings)
        self.assertEqual(actual_state, constants.AdGroupSourceSettingsState.INACTIVE)

        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE
        ad_group_settings_copy = ad_group_settings_copy.copy_settings()
        ad_group_settings_copy.state = constants.AdGroupSettingsState.INACTIVE
        ad_group_settings_copy.save(None)
        actual_state = self.settings_state_consistency._get_actual_source_settings_state(ad_group_source_settings)
        self.assertEqual(actual_state, constants.AdGroupSourceSettingsState.INACTIVE)
