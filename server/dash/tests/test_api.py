import decimal

from django.test import TestCase

from dash import models as dashmodels
from dash import constants as dashconstants
from dash import api


class CampaignStatusApiTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_network = dashmodels.AdGroupNetwork.objects.get(id=1)

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

        new_state = dashconstants.AdGroupNetworkSettingsState.INACTIVE

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
