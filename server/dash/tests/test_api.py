import decimal
import datetime

from django.test import TestCase

from dash import models
from dash import constants
from dash import api


class CampaignStatusApiTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_network = models.AdGroupNetwork.objects.get(id=1)

    def test_upsert_unmodified(self):
        current_settings = self.ad_group_network.settings.latest()

        api.campaign_status_upsert(self.ad_group_network, {
            'cpc_cc': int(current_settings.cpc_cc * 10000),
            'daily_budget_cc': int(current_settings.daily_budget_cc * 10000),
            'state': current_settings.state,
        })

        self.assertEqual(current_settings, self.ad_group_network.settings.latest())

    def test_upsert_modified_state(self):
        current_settings = self.ad_group_network.settings.latest()

        new_state = constants.AdGroupNetworkSettingsState.INACTIVE

        api.campaign_status_upsert(self.ad_group_network, {
            'cpc_cc': int(current_settings.cpc_cc * 10000),
            'daily_budget_cc': int(current_settings.daily_budget_cc * 10000),
            'state': new_state,
        })

        self.assertNotEqual(current_settings, self.ad_group_network.settings.latest())
        self.assertEqual(self.ad_group_network.settings.latest().state, new_state)

    def test_upsert_modified_cpc(self):
        current_settings = self.ad_group_network.settings.latest()

        new_cpc_cc = 1234

        api.campaign_status_upsert(self.ad_group_network, {
            'cpc_cc': new_cpc_cc,
            'daily_budget_cc': int(current_settings.daily_budget_cc * 10000),
            'state': current_settings.state,
        })

        self.assertNotEqual(current_settings, self.ad_group_network.settings.latest())
        self.assertEqual(self.ad_group_network.settings.latest().cpc_cc, decimal.Decimal(new_cpc_cc) / 10000)

    def test_upsert_modified_daily_budget(self):
        current_settings = self.ad_group_network.settings.latest()

        new_daily_budget_cc = 1234

        api.campaign_status_upsert(self.ad_group_network, {
            'cpc_cc': int(current_settings.cpc_cc * 10000),
            'daily_budget_cc': new_daily_budget_cc,
            'state': current_settings.state,
        })

        self.assertNotEqual(current_settings, self.ad_group_network.settings.latest())
        self.assertEqual(
            self.ad_group_network.settings.latest().daily_budget_cc,
            decimal.Decimal(new_daily_budget_cc) / 10000
        )

    def test_update_campaign_state_unmodified(self):
        current_settings = self.ad_group_network.settings.latest()
        state = current_settings.state
        api.update_campaign_state(self.ad_group_network, state)
        self.assertEqual(current_settings, self.ad_group_network.settings.latest())

    def test_update_campaign_state_modified(self):
        current_settings = self.ad_group_network.settings.latest()
        new_state = current_settings.state % 2 + 1
        api.update_campaign_state(self.ad_group_network, new_state)
        self.assertNotEqual(current_settings, self.ad_group_network.settings.latest())
        self.assertEqual(self.ad_group_network.settings.latest().state, new_state)


class AdGroupSettingsOrderTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_network = models.AdGroupNetwork.objects.get(id=1)

    def test_settings_changes(self):

        set1 = models.AdGroupSettings(
            created_dt=datetime.date.today(),

            state=1,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.1'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        set2 = models.AdGroupSettings(
            created_dt=datetime.date.today() - datetime.timedelta(days=1),

            state=2,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.2'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        self.assertEqual(api._get_setting_changes(set1, set1), {})

        self.assertEqual(
            api._get_setting_changes(set1, set2),
            {'state': 2, 'cpc_cc': decimal.Decimal('0.2')},
        )
